import os
import shutil
import datetime
import xml.etree.ElementTree as ET

from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import selectinload
from db.models import Group, Photo
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("URL")

YML_PATH = "data/export.yml"
YML_BACKUP_DIR = "data/yml_backups"

async def sync_yml_from_path(session, file_path):
    with open(file_path, "rb") as f:
        content = f.read()

    root = ET.fromstring(content)
    offers = root.find("shop").find("offers")

    existing_groups = {g.name: g for g in (await session.scalars(select(Group))).all()}

    for offer in offers.findall("offer"):
        name = offer.find("name").text
        available = offer.get("available") == "true"

        group = existing_groups.get(name)
        if not group:
            group = Group(name=name)
            session.add(group)
        group.available = available

    await session.commit()
async def sync_yml(session, yml_file_path=None):
    """
    Синхронизирует базу из YML файла.
    Если yml_file_path не задан — использует URL для скачивания.
    """
    if yml_file_path:
        with open(yml_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        root = ET.fromstring(content)
    else:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        URL = os.getenv("URL")
        if not URL:
            raise ValueError("❌ URL не задан")
        response = requests.get(URL)
        response.raise_for_status()
        root = ET.fromstring(response.content)

    offers = root.find("shop").find("offers")
    existing_groups = {g.name: g for g in (await session.scalars(select(Group))).all()}

    for offer in offers.findall("offer"):
        name = offer.find("name").text
        available = offer.get("available") == "true"

        group = existing_groups.get(name)
        if not group:
            group = Group(name=name)
            session.add(group)
        group.available = available

    await session.commit()



async def get_groups_with_photo_counts(session):
    """Получить группы с количеством фото."""
    result = await session.execute(
        select(Group.id, Group.name, func.count(Photo.id).label("count"))
        .join(Photo, isouter=True)
        .group_by(Group.id)
    )
    return [type("GroupInfo", (), dict(id=row[0], name=row[1], count=row[2])) for row in result.all()]


async def get_photos_by_group(session, group_id):
    """Получить фото по группе."""
    result = await session.execute(select(Photo).where(Photo.group_id == group_id))
    return result.scalars().all()


async def get_group(session, group_id):
    return await session.get(Group, group_id)


async def create_group(session, name: str):
    group = Group(name=name)
    session.add(group)
    await session.commit()
    return group


async def update_group(session, group_id: int, name: str):
    await session.execute(update(Group).where(Group.id == group_id).values(name=name))
    await session.commit()


async def delete_group(session, group_id: int):
    await session.execute(delete(Group).where(Group.id == group_id))
    await session.commit()


async def get_photo(session, photo_id):
    return await session.get(Photo, photo_id)


async def add_photo(session, group_id: int, name: str, file_path: str):
    photo = Photo(name=name, file_path=file_path, group_id=group_id)
    session.add(photo)
    await session.commit()
    return photo


async def update_photo(session, photo_id: int, name: str, file_path: str):
    await session.execute(update(Photo).where(Photo.id == photo_id).values(name=name, file_path=file_path))
    await session.commit()


async def delete_photo(session, photo_id: int):
    await session.execute(delete(Photo).where(Photo.id == photo_id))
    await session.commit()


async def update_yml(session):
    """Создать/обновить YML-файл из БД и сделать бэкап."""
    os.makedirs(YML_BACKUP_DIR, exist_ok=True)
    if os.path.exists(YML_PATH):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(YML_PATH, os.path.join(YML_BACKUP_DIR, f"backup_{timestamp}.yml"))

    result = await session.execute(select(Group).options(selectinload(Group.photos)))
    groups = result.scalars().all()

    with open(YML_PATH, "w", encoding="utf-8") as f:
        for group in groups:
            f.write(f"- group: {group.name}\n")
            for photo in group.photos:
                f.write(f"  - name: {photo.name}\n")
                f.write(f"    file_path: {photo.file_path}\n")


async def restore_yml(backup_filename: str):
    """Восстановить YML из бэкапа."""
    src = os.path.join(YML_BACKUP_DIR, backup_filename)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Backup file {backup_filename} not found")
    shutil.copy(src, YML_PATH)
