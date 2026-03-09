"""
API 测试：项目管理 REST API

测试 5 个 CRUD 端点:
- GET /api/projects - 列出项目
- POST /api/projects - 创建项目
- GET /api/projects/<id> - 获取项目详情
- PUT /api/projects/<id> - 更新项目
- DELETE /api/projects/<id> - 删除项目
"""
import pytest

from app.database import db
from app.models.db_models import ProjectDB


class TestListProjects:
    """测试 GET /api/projects"""

    def test_list_projects_empty(self, test_client):
        """测试空列表"""
        response = test_client.get('/api/projects')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['projects'] == []
        assert data['total'] == 0

    def test_list_projects_with_data(self, test_client, test_app):
        """测试有数据"""
        with test_app.app_context():
            project1 = ProjectDB(name="项目1")
            project2 = ProjectDB(name="项目2")
            db.session.add_all([project1, project2])
            db.session.commit()
        
        response = test_client.get('/api/projects')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['projects']) == 2
        assert data['total'] == 2

    def test_list_projects_pagination(self, test_client, test_app):
        """测试分页"""
        with test_app.app_context():
            for i in range(25):
                project = ProjectDB(name=f"项目{i}")
                db.session.add(project)
            db.session.commit()
        
        response = test_client.get('/api/projects?page=2&per_page=10')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['projects']) == 10
        assert data['page'] == 2
        assert data['per_page'] == 10
        assert data['total'] == 25


class TestCreateProject:
    """测试 POST /api/projects"""

    def test_create_project_success(self, test_client):
        """测试创建成功"""
        response = test_client.post('/api/projects', 
            json={'name': '测试项目', 'description': '测试描述'},
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == '测试项目'
        assert data['description'] == '测试描述'
        assert 'id' in data
        assert 'created_at' in data

    def test_create_project_without_description(self, test_client):
        """测试无描述创建"""
        response = test_client.post('/api/projects',
            json={'name': '仅名称'},
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == '仅名称'
        assert data['description'] == ''

    def test_create_project_missing_name(self, test_client):
        """测试缺少名称"""
        response = test_client.post('/api/projects',
            json={'description': '无名称'},
            content_type='application/json'
        )
        
        assert response.status_code == 400

    def test_create_project_empty_body(self, test_client):
        """测试空请求体"""
        response = test_client.post('/api/projects',
            json=None,
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestGetProject:
    """测试 GET /api/projects/<id>"""

    def test_get_project_success(self, test_client, test_app):
        """测试获取成功"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目", description="描述")
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        response = test_client.get(f'/api/projects/{project_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == project_id
        assert data['name'] == '测试项目'
        assert data['description'] == '描述'

    def test_get_project_not_found(self, test_client):
        """测试项目不存在"""
        response = test_client.get('/api/projects/99999')
        
        assert response.status_code == 404


class TestUpdateProject:
    """测试 PUT /api/projects/<id>"""

    def test_update_project_success(self, test_client, test_app):
        """测试更新成功"""
        with test_app.app_context():
            project = ProjectDB(name="旧名称", description="旧描述")
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        response = test_client.put(f'/api/projects/{project_id}',
            json={'name': '新名称', 'description': '新描述'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == '新名称'
        assert data['description'] == '新描述'

    def test_update_project_partial(self, test_client, test_app):
        """测试部分更新"""
        with test_app.app_context():
            project = ProjectDB(name="名称", description="描述")
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        response = test_client.put(f'/api/projects/{project_id}',
            json={'name': '新名称'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == '新名称'
        assert data['description'] == '描述'

    def test_update_project_not_found(self, test_client):
        """测试更新不存在的项目"""
        response = test_client.put('/api/projects/99999',
            json={'name': '新名称'},
            content_type='application/json'
        )
        
        assert response.status_code == 404

    def test_update_project_empty_body(self, test_client, test_app):
        """测试空请求体"""
        with test_app.app_context():
            project = ProjectDB(name="测试")
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        response = test_client.put(f'/api/projects/{project_id}',
            json={},
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestDeleteProject:
    """测试 DELETE /api/projects/<id>"""

    def test_delete_project_success(self, test_client, test_app):
        """测试删除成功"""
        with test_app.app_context():
            project = ProjectDB(name="待删除项目")
            db.session.add(project)
            db.session.commit()
            project_id = project.id
        
        response = test_client.delete(f'/api/projects/{project_id}')
        
        assert response.status_code == 200
        
        with test_app.app_context():
            deleted = ProjectDB.query.get(project_id)
            assert deleted is None

    def test_delete_project_not_found(self, test_client):
        """测试删除不存在的项目"""
        response = test_client.delete('/api/projects/99999')
        
        assert response.status_code == 404


class TestProjectAPIIntegration:
    """API 集成测试"""

    def test_full_crud_workflow(self, test_client):
        """测试完整 CRUD 流程"""
        create_resp = test_client.post('/api/projects',
            json={'name': '集成测试项目', 'description': '初始描述'},
            content_type='application/json'
        )
        assert create_resp.status_code == 201
        project_id = create_resp.get_json()['id']
        
        get_resp = test_client.get(f'/api/projects/{project_id}')
        assert get_resp.status_code == 200
        assert get_resp.get_json()['name'] == '集成测试项目'
        
        update_resp = test_client.put(f'/api/projects/{project_id}',
            json={'name': '更新后项目'},
            content_type='application/json'
        )
        assert update_resp.status_code == 200
        assert update_resp.get_json()['name'] == '更新后项目'
        
        delete_resp = test_client.delete(f'/api/projects/{project_id}')
        assert delete_resp.status_code == 200
        
        get_deleted = test_client.get(f'/api/projects/{project_id}')
        assert get_deleted.status_code == 404

    def test_multiple_projects_workflow(self, test_client):
        """测试多项目工作流"""
        for i in range(3):
            resp = test_client.post('/api/projects',
                json={'name': f'项目{i}'},
                content_type='application/json'
            )
            assert resp.status_code == 201
        
        list_resp = test_client.get('/api/projects')
        assert list_resp.status_code == 200
        assert len(list_resp.get_json()['projects']) == 3
