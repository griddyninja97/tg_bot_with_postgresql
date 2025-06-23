from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

GROUPS_PER_PAGE = 10
def main_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Загрузить YML")],
            [KeyboardButton(text="📁 Список групп")],
            [KeyboardButton(text="⚙️ Управление YML")]
        ],
        resize_keyboard=True
    )
    return kb

def yml_management_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Синхронизировать YML")],
            [KeyboardButton(text="💾 Сохранить копию YML")],
            [KeyboardButton(text="⏪ Откатить YML")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    return kb


def groups_keyboard(groups, page=0):
    kb = InlineKeyboardBuilder()
    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE
    page_groups = groups[start:end]

    for group in page_groups:
        kb.button(text=f"{group.name} ({group.count})", callback_data=f"group:{group.id}")

    buttons_nav = []
    if page > 0:
        buttons_nav.append(("⬅️ Назад", f"groups_page:{page-1}"))
    if end < len(groups):
        buttons_nav.append(("➡️ Вперёд", f"groups_page:{page+1}"))
    for text, data in buttons_nav:
        kb.button(text=text, callback_data=data)

    return kb.as_markup()

def group_photos_keyboard(group_id, photos):
    """
    Клавиатура управления фотками группы.
    photos — список объектов с .id и .name
    """
    kb = InlineKeyboardBuilder()
    for photo in photos:
        kb.button(text=photo.name, callback_data=f"photo:{photo.id}")
    kb.button(text="Добавить фото ➕", callback_data=f"add_photo:{group_id}")
    kb.button(text="Назад ⬅️", callback_data="groups_list")
    return kb.as_markup()

def yml_management_inline_keyboard():
    """
    Клавиатура управления YML.
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="Синхронизировать YML 🔄", callback_data="sync_yml")
    kb.button(text="Сохранить копию YML 💾", callback_data="save_yml_backup")
    kb.button(text="Откатить YML ⏪", callback_data="restore_yml")
    return kb.as_markup()

def confirmation_keyboard(action: str):
    """
    Клавиатура подтверждения действия.
    action — строка для callback_data, например 'delete_photo:123'
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="Да ✅", callback_data=f"confirm:{action}")
    kb.button(text="Нет ❌", callback_data="cancel")
    return kb.as_markup()

get_groups_kb = groups_keyboard
get_manage_kb = yml_management_keyboard
