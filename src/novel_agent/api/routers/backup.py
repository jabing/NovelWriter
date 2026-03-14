"""Backup and Restore API endpoints.

This module provides endpoints for exporting and importing novel data.
"""

import io
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from src.novel_agent import DATA_DIR, NOVELS_DIR, OPENVIKING_DIR

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export")
async def export_all() -> StreamingResponse:
    """Export all novel data as a ZIP file.
    
    Creates a compressed archive containing:
    - All novel projects
    - Chapters and content
    - Character profiles
    - Outline data
    - Settings and metadata
    
    Returns:
        ZIP file download response
    """
    try:
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Export novels directory
            if NOVELS_DIR.exists():
                for novel_dir in NOVELS_DIR.iterdir():
                    if novel_dir.is_dir():
                        novel_name = novel_dir.name
                        
                        # Add novel metadata
                        metadata_file = novel_dir / "metadata.json"
                        if metadata_file.exists():
                            zip_file.write(
                                metadata_file,
                                f"novels/{novel_name}/metadata.json"
                            )
                        
                        # Add chapters
                        chapters_dir = novel_dir / "chapters"
                        if chapters_dir.exists():
                            for chapter_file in chapters_dir.glob("*.json"):
                                zip_file.write(
                                    chapter_file,
                                    f"novels/{novel_name}/chapters/{chapter_file.name}"
                                )
                            for chapter_file in chapters_dir.glob("*.md"):
                                zip_file.write(
                                    chapter_file,
                                    f"novels/{novel_name}/chapters/{chapter_file.name}"
                                )
                        
                        # Add characters
                        characters_dir = novel_dir / "characters"
                        if characters_dir.exists():
                            for char_file in characters_dir.glob("*.json"):
                                zip_file.write(
                                    char_file,
                                    f"novels/{novel_name}/characters/{char_file.name}"
                                )
                        
                        # Add outlines
                        outlines_dir = novel_dir / "outlines"
                        if outlines_dir.exists():
                            for outline_file in outlines_dir.glob("*.json"):
                                zip_file.write(
                                    outline_file,
                                    f"novels/{novel_name}/outlines/{outline_file.name}"
                                )
            
            # Export OpenViking data
            if OPENVIKING_DIR.exists():
                for item in OPENVIKING_DIR.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(OPENVIKING_DIR)
                        zip_file.write(
                            item,
                            f"openviking/{relative_path}"
                        )
            
            # Add export manifest
            manifest = {
                "export_date": datetime.now().isoformat(),
                "version": "1.0.0",
                "source": "NovelWriter"
            }
            zip_file.writestr(
                "manifest.json",
                f"{{\n  \"export_date\": \"{manifest['export_date']}\",\n  \"version\": \"{manifest['version']}\",\n  \"source\": \"{manifest['source']}\"\n}}"
            )
        
        # Prepare buffer for streaming
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="novelwriter_backup_{timestamp}.zip"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import")
async def import_all(file: UploadFile = File(...)) -> JSONResponse:
    """Import and restore data from a ZIP backup file.
    
    Args:
        file: ZIP file containing backup data
        
    Returns:
        JSON response with import status and summary
    """
    try:
        # Validate file type
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")
        
        # Read uploaded file
        contents = await file.read()
        zip_buffer = io.BytesIO(contents)
        
        imported_stats = {
            "novels": 0,
            "chapters": 0,
            "characters": 0,
            "outlines": 0
        }
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
            # Verify manifest
            if "manifest.json" not in zip_file.namelist():
                raise HTTPException(
                    status_code=400,
                    detail="Invalid backup file: manifest.json not found"
                )
            
            # Extract all files
            for file_path in zip_file.namelist():
                if file_path.endswith('/'):
                    continue  # Skip directories
                
                # Determine target path
                if file_path.startswith("novels/"):
                    # Extract to novels directory
                    target_path = NOVELS_DIR / file_path[7:]  # Remove "novels/" prefix
                    imported_stats["novels"] += 1 if "/chapters/" not in file_path and "/characters/" not in file_path else 0
                    if "chapters/" in file_path:
                        imported_stats["chapters"] += 1
                    elif "characters/" in file_path:
                        imported_stats["characters"] += 1
                    elif "outlines/" in file_path:
                        imported_stats["outlines"] += 1
                elif file_path.startswith("openviking/"):
                    # Extract to OpenViking directory
                    target_path = OPENVIKING_DIR / file_path[11:]  # Remove "openviking/" prefix
                else:
                    continue  # Skip other files
                
                # Create parent directories
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Extract file
                with zip_file.open(file_path) as source:
                    with open(target_path, 'wb') as target:
                        target.write(source.read())
        
        return JSONResponse({
            "success": True,
            "message": "Backup imported successfully",
            "imported": imported_stats
        })
    except HTTPException:
        raise
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/status")
async def backup_status() -> dict[str, Any]:
    """Get backup status and available backups.
    
    Returns:
        Dictionary with backup statistics and available backup files
    """
    try:
        backups_dir = DATA_DIR / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        
        # List available backup files
        backup_files = []
        if backups_dir.exists():
            for backup_file in backups_dir.glob("*.zip"):
                stat = backup_file.stat()
                backup_files.append({
                    "name": backup_file.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Count current data
        novel_count = sum(1 for d in NOVELS_DIR.iterdir() if d.is_dir()) if NOVELS_DIR.exists() else 0
        
        chapter_count = 0
        if NOVELS_DIR.exists():
            for novel_dir in NOVELS_DIR.iterdir():
                if novel_dir.is_dir():
                    chapters_dir = novel_dir / "chapters"
                    if chapters_dir.exists():
                        chapter_count += sum(1 for _ in chapters_dir.glob("*.json"))
                        chapter_count += sum(1 for _ in chapters_dir.glob("*.md"))
        
        character_count = 0
        if NOVELS_DIR.exists():
            for novel_dir in NOVELS_DIR.iterdir():
                if novel_dir.is_dir():
                    characters_dir = novel_dir / "characters"
                    if characters_dir.exists():
                        character_count += sum(1 for _ in characters_dir.glob("*.json"))
        
        return {
            "backup_files": sorted(backup_files, key=lambda x: x["created"], reverse=True),
            "current_data": {
                "novels": novel_count,
                "chapters": chapter_count,
                "characters": character_count
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "backup_files": [],
            "current_data": {
                "novels": 0,
                "chapters": 0,
                "characters": 0
            }
        }
