from aiogram import Router, F
from aiogram.types import Message, InputFile, CallbackQuery
from aiogram.filters import Command
from db.crud import (
    sync_yml, get_groups_with_photo_counts, get_photos_by_group,
    add_photo, delete_photo, update_photo,sync_yml_from_path
)
from db.session import async_session
from bot.keyboard import main_keyboard, yml_management_keyboard, groups_keyboard, group_photos_keyboard, confirmation_keyboard
import os
import aiohttp
from db.crud import YML_BACKUP_DIR

router = Router()

@router.message(F.text.startswith("http"))
async def receive_yml_url(message: Message):
    url = message.text.strip()

    await message.answer("⏳ Скачиваю файл...")

    try:
        import aiohttp
        import os
        file_path = "data/temp_download.yml"
        os.makedirs("data", exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await message.answer(f"❌ Ошибка загрузки файла, статус {resp.status}")
                    return
                content = await resp.read()

        import xml.etree.ElementTree as ET
        try:
            ET.fromstring(content)
        except ET.ParseError:
            await message.answer("❌ Полученный файл не является валидным XML/YML")
            return

        with open(file_path, "wb") as f:
            f.write(content)

        async with async_session() as db_session:
            await sync_yml_from_path(db_session, file_path)

        await message.answer("✅ База успешно обновлена из файла по ссылке!")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

    
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Выбери действие:", reply_markup=main_keyboard())

@router.message(F.text == "📥 Загрузить YML")
async def ask_upload_yml(message: Message):
    await message.answer("Пришли мне файл YML для обновления базы.")

@router.message(F.content_type == "document")
async def receive_yml_file(message: Message):
    document = message.document
    if not (document.file_name.endswith(".yml") or document.file_name.endswith(".yaml")):
        await message.answer("❌ Это не YML файл, попробуй ещё раз.")
        return

    file_path = f"data/{document.file_name}"
    await message.document.download(destination_file=file_path)

    async with async_session() as session:
        try:
            await sync_yml(session, file_path)
        except Exception as e:
            await message.answer(f"Ошибка при синхронизации: {e}")
            return

    await message.answer("✅ База успешно обновлена из YML!", reply_markup=main_keyboard())

@router.message(F.text == "📁 Список групп")
async def list_groups(message: Message):
    async with async_session() as session:
        groups = await get_groups_with_photo_counts(session)
    if not groups:
        await message.answer("Пока групп нет.")
        return
    kb = groups_keyboard(groups, page=0)
    await message.answer("Выберите группу:", reply_markup=kb)


@router.callback_query(F.data.startswith("group:"))
async def show_group_photos(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        photos = await get_photos_by_group(session, group_id)

    if not photos:
        await callback.message.answer("❌ Фото не найдены")
        return

    await callback.message.answer(f"Фото группы:", reply_markup=group_photos_keyboard(group_id, photos))
    
@router.callback_query(F.data.startswith("groups_page:"))
async def groups_page_callback(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    async with async_session() as session:
        groups = await get_groups_with_photo_counts(session)
    kb = groups_keyboard(groups, page)
    await callback.message.edit_text("Выберите группу:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("add_photo:"))
async def add_photo_prompt(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])
    await callback.message.answer(f"Пришли фото для группы с id {group_id}. (Загрузить через прикреплённый файл)")
    # Здесь надо будет ввести FSM для приёма файла и названия

@router.callback_query(F.data.startswith("delete_photo:"))
async def delete_photo_confirm(callback: CallbackQuery):
    photo_id = int(callback.data.split(":")[1])
    await callback.message.answer("Подтверждаешь удаление фото?", reply_markup=confirmation_keyboard(f"delete_photo:{photo_id}"))

@router.callback_query(F.data.startswith("confirm:"))
async def process_confirm(callback: CallbackQuery):
    action = callback.data.split(":", 1)[1]

    async with async_session() as session:
        if action.startswith("delete_photo:"):
            photo_id = int(action.split(":")[1])
            await delete_photo(session, photo_id)
            await callback.message.answer("Фото удалено.")
        # Здесь можно добавить другие подтверждения

    await callback.message.delete_reply_markup()

@router.callback_query(F.data == "groups_list")
async def back_to_groups(callback: CallbackQuery):
    async with async_session() as session:
        groups = await get_groups_with_photo_counts(session)
    await callback.message.answer("Выберите группу:", reply_markup=groups_keyboard(groups))

@router.message(F.text == "⚙️ Управление YML")
async def yml_management(message: Message):
    await message.answer("Управление YML файлами:", reply_markup=yml_management_keyboard())

@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    await message.answer("Возврат в главное меню.", reply_markup=main_keyboard())

@router.message(F.text == "🔄 Синхронизировать YML")
async def manual_sync(message: Message):
    async with async_session() as session:
        try:
            await sync_yml(session)
            await message.answer("✅ Синхронизация YML завершена.", reply_markup=main_keyboard())
        except Exception as e:
            await message.answer(f"Ошибка при синхронизации: {e}")

@router.message(F.text == "💾 Сохранить копию YML")
async def save_backup(message: Message):
    await message.answer("Функция сохранения копии пока не реализована.", reply_markup=yml_management_keyboard())

@router.message(F.text == "⏪ Откатить YML")
async def restore_backup(message: Message):
    try:
        backups = sorted(os.listdir(YML_BACKUP_DIR), reverse=True)
    except FileNotFoundError:
        await message.answer("Бэкапы не найдены.", reply_markup=yml_management_keyboard())
        return

    if not backups:
        await message.answer("Бэкапы не найдены.", reply_markup=yml_management_keyboard())
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for fname in backups:
        kb.button(text=fname, callback_data=f"restore_yml:{fname}")
    await message.answer("Выберите бэкап для восстановления:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("restore_yml:"))
async def restore_yml_callback(callback: CallbackQuery):
    backup_filename = callback.data.split(":", 1)[1]
    try:
        await restore_yml(backup_filename)
        await callback.message.answer(f"✅ YML успешно восстановлен из {backup_filename}", reply_markup=yml_management_keyboard())
    except Exception as e:
        await callback.message.answer(f"Ошибка при восстановлении: {e}", reply_markup=yml_management_keyboard())
    await callback.answer()
