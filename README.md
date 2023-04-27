### Социальная сеть для блоггеров
Социальаня сеть, в которой пользователи размещают свои текстовые посты. Посты могут сопровождаться размещением изображения. 

### Используемые технологии
- Django 3.2.16
- djangorestframework 3.12.4
- djangorestframework-simplejwt 4.7.2
- Pillow 9.3.0

### Как запустить проект
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://git@github.com:DmitryOstrovskiy/api_yatube.git
```
cd api_yatube
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
source venv/Scripts/activate
```
Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
```
pip install -r requirements.txt
```
Выполнить миграции:
```
python manage.py migrate
```
Запустить проект:
```
python manage.py runserver
