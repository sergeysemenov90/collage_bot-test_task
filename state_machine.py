from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InputFile, Message
from collage_creator import make_collage
from make_bot import bot, dp
from keyboard import kb_collage_get
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove


root='C:/Users/semen/PycharmProjects/GreatCollage/media/'


class FSMAdmin(StatesGroup):
    resolution = State()
    photos = State()
    making_collage = State()
    again = State()


# Начало диалога для создания коллажа
async def collage_start(message: Message):
    await FSMAdmin.resolution.set()
    await message.reply('Выбери необходимое разрешение коллажа', reply_markup=ReplyKeyboardRemove())


# Получаем первый ответ от пользователя с разрешением коллажа, записываем в словарь
async def collage_get_resolution(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['resolution'] = message.text
    await FSMAdmin.next()
    await message.reply('Отлично! Теперь загрузи до 10 фотографий для создания коллажа')


# Получаем второй ответ с фотографиями, загружаем их адреса в словарь
photos = []
async def collage_get_photos(message: Message, state: FSMContext):
    user_id = message.from_user.id
    file = await bot.get_file(message.photo[-1].file_id)
    file_path = file.file_path
    photos.append(f'{root}{user_id}/{file_path}')
    async with state.proxy() as data:
        data['photos'] = photos
        data['user'] = user_id
    await bot.download_file(file_path, destination_dir=f'media/{user_id}')
    await FSMAdmin.making_collage.set()
    await message.answer('загружаю...', reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).insert(kb_collage_get))


async def collage_making_collage(message: Message, state: FSMContext):
    print('Making_collage')
    async with state.proxy() as data:
        await make_collage(data['photos'], 'new_collage.jpg', 1600, 500)
        await bot.send_message(data['user'], 'Фотографии получены! готовлю результат.....')
    await bot.send_photo(data['user'], InputFile('new_collage.jpg'), reply_markup=ReplyKeyboardRemove())
    await FSMAdmin.next()


# Снова генерируем и отправляем коллаж, если пользователь хочет попробовать
async def collage_get_photos_again(message: Message, state: FSMContext):
    await message.reply('Пробую еще раз....')
    async with state.proxy() as data:
        await make_collage(data['photos'], 'new_collage.jpg', 1600, 500, shuffle_list=True)
    await bot.send_photo(message.from_user.id, InputFile('new_collage.jpg'))
    await state.finish()


# Регистрируем хендлеры
def register_handlers_state_machine(dp:Dispatcher):
    dp.register_message_handler(collage_start, commands=['Начать!'], state=None)
    dp.register_message_handler(collage_get_resolution, state=FSMAdmin.resolution)
    dp.register_message_handler(collage_get_photos, content_types=['photo'], state=FSMAdmin.photos)
    dp.register_message_handler(collage_making_collage, commands=['get', 'Получить_коллаж!'], state=FSMAdmin.making_collage)
    dp.register_message_handler(collage_get_photos_again, commands='again', state=FSMAdmin.again)
