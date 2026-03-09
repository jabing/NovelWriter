"""
单元测试：ProjectDB 数据库模型

测试项目模型的 CRUD 操作、字段和关系
"""
import pytest
from datetime import datetime

from app.models.db_models import ProjectDB, CharacterDB, StoryEventDB
from app.database import db


class TestProjectDBModel:
    """测试 ProjectDB 模型"""

    def test_project_db_fields(self):
        """测试字段存在性"""
        project = ProjectDB(name="测试项目")
        
        assert hasattr(project, 'id')
        assert hasattr(project, 'name')
        assert hasattr(project, 'description')
        assert hasattr(project, 'created_at')
        assert hasattr(project, 'updated_at')

    def test_project_db_default_values(self, test_app):
        """测试默认值"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目")
            db.session.add(project)
            db.session.commit()
            
            assert project.name == "测试项目"
            assert project.description == ""
            assert project.created_at is not None
            assert project.updated_at is not None

    def test_project_db_with_values(self):
        """测试自定义值"""
        project = ProjectDB(
            name="悬疑小说",
            description="一个关于谋杀案的悬疑故事"
        )
        
        assert project.name == "悬疑小说"
        assert project.description == "一个关于谋杀案的悬疑故事"

    def test_project_db_timestamps(self, test_app):
        """测试时间戳自动生成"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目")
            db.session.add(project)
            db.session.commit()
            
            assert project.created_at is not None
            assert project.updated_at is not None
            
            datetime.fromisoformat(project.created_at)
            datetime.fromisoformat(project.updated_at)

    def test_project_db_repr(self):
        """测试字符串表示"""
        project = ProjectDB(name="测试项目")
        
        assert repr(project) == '<Project 测试项目>'


class TestProjectDBRelationships:
    """测试 ProjectDB 关系映射"""

    def test_project_has_characters_relationship(self):
        """测试项目-角色关系"""
        project = ProjectDB(name="测试项目")
        
        assert hasattr(project, 'characters')
        assert project.characters == []

    def test_project_has_events_relationship(self):
        """测试项目-事件关系"""
        project = ProjectDB(name="测试项目")
        
        assert hasattr(project, 'events')
        assert project.events == []


class TestProjectDBWithApp:
    """需要 Flask 应用上下文的测试"""

    def test_create_project(self, test_app):
        """测试创建项目"""
        with test_app.app_context():
            project = ProjectDB(name="新项目", description="项目描述")
            db.session.add(project)
            db.session.commit()
            
            assert project.id is not None
            assert project.name == "新项目"
            assert project.description == "项目描述"

    def test_read_project(self, test_app):
        """测试读取项目"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目", description="测试描述")
            db.session.add(project)
            db.session.commit()
            
            saved_project = ProjectDB.query.filter_by(name="测试项目").first()
            
            assert saved_project is not None
            assert saved_project.name == "测试项目"
            assert saved_project.description == "测试描述"

    def test_update_project(self, test_app):
        """测试更新项目"""
        with test_app.app_context():
            project = ProjectDB(name="旧名称", description="旧描述")
            db.session.add(project)
            db.session.commit()
            
            project.name = "新名称"
            project.description = "新描述"
            db.session.commit()
            
            updated_project = ProjectDB.query.get(project.id)
            assert updated_project.name == "新名称"
            assert updated_project.description == "新描述"

    def test_delete_project(self, test_app):
        """测试删除项目"""
        with test_app.app_context():
            project = ProjectDB(name="待删除项目")
            db.session.add(project)
            db.session.commit()
            
            project_id = project.id
            
            db.session.delete(project)
            db.session.commit()
            
            deleted_project = ProjectDB.query.get(project_id)
            assert deleted_project is None

    def test_project_with_characters(self, test_app):
        """测试项目包含角色"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目")
            db.session.add(project)
            db.session.commit()
            
            character = CharacterDB(
                entity_id="char-001",
                name="主角",
                project_id=project.id
            )
            db.session.add(character)
            db.session.commit()
            
            saved_project = ProjectDB.query.get(project.id)
            assert len(saved_project.characters) == 1
            assert saved_project.characters[0].name == "主角"

    def test_project_with_events(self, test_app):
        """测试项目包含事件"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目")
            db.session.add(project)
            db.session.commit()
            
            event = StoryEventDB(
                entity_id="event-001",
                name="关键事件",
                project_id=project.id
            )
            db.session.add(event)
            db.session.commit()
            
            saved_project = ProjectDB.query.get(project.id)
            assert len(saved_project.events) == 1
            assert saved_project.events[0].name == "关键事件"

    def test_multiple_projects(self, test_app):
        """测试多个项目"""
        with test_app.app_context():
            project1 = ProjectDB(name="项目1")
            project2 = ProjectDB(name="项目2")
            project3 = ProjectDB(name="项目3")
            
            db.session.add_all([project1, project2, project3])
            db.session.commit()
            
            projects = ProjectDB.query.all()
            assert len(projects) == 3
            assert {p.name for p in projects} == {"项目1", "项目2", "项目3"}


class TestProjectDBValidation:
    """测试项目验证"""

    def test_project_name_required(self, test_app):
        """测试项目名称必填"""
        with test_app.app_context():
            project = ProjectDB(description="没有名称")
            db.session.add(project)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()

    def test_project_empty_description(self, test_app):
        """测试空描述"""
        with test_app.app_context():
            project = ProjectDB(name="测试项目", description="")
            db.session.add(project)
            db.session.commit()
            
            assert project.description == ""

    def test_project_long_description(self, test_app):
        """测试长描述"""
        with test_app.app_context():
            long_desc = "这是一个很长的描述。" * 100
            project = ProjectDB(name="测试项目", description=long_desc)
            db.session.add(project)
            db.session.commit()
            
            assert len(project.description) == len(long_desc)
