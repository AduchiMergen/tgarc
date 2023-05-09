#!/usr/bin/env python3

import configparser
import datetime
import json
import os

import click

from pathlib import Path

from pick import Option, pick
from pyrogram import Client
from pyrogram.types import Object, User


MESSAGE_LIMIT = 100


@click.group()
def cli():
    """Утилита командной строки собирающая все публикации из телеграм каналов по списку и сохраняющая в JSONL формате"""
    pass


def get_work_dir():
    work_dir = Path.home() / '.tgarc'
    work_dir.mkdir(exist_ok=True)
    return work_dir


def get_config_path():
    return get_work_dir() / 'config'


def get_update_path():
    return get_work_dir() / 'update'


def get_pyrogram_client():
    config = configparser.ConfigParser()
    config.read(get_config_path())
    return Client(
        "tgarc",
        workdir=str(get_work_dir()),
        api_id=config['pyrogram']['api_id'],
        api_hash=config['pyrogram']['api_hash'],
    )


@cli.command()
@click.option('--api_id', prompt=True, type=int)
@click.option('--api_hash', prompt=True)
def configure(api_id, api_hash):
    """
    Настроить ключи подключения, логин и пароль
    """
    config = configparser.ConfigParser()
    config['pyrogram'] = {
        'api_id': api_id,
        'api_hash': api_hash,
    }
    with open(get_config_path(), 'w') as configfile:
        config.write(configfile)
    with get_pyrogram_client() as app:
        me = app.get_me()
        click.echo(f'Logged as {me.first_name} {me.last_name} @{me.username}')


def show_params(user: User, kwargs):
    click.echo(f"""
    Archive tg channels and chats.
    
    [{'+' if kwargs.get('video') else ' '}] Download video
    [{'+' if kwargs.get('pictures') else ' '}] Download pictures
    [{'+' if kwargs.get('files') else ' '}] Download files ('audio', 'document', 'sticker', 'animation', 'voice', 'video_note')
    
    Download file max size: {kwargs.get('max_size')+' MB' if kwargs.get('max_size') else 'infinite'}
    
    Output format: {kwargs.get('format')}
    Output dir: {kwargs.get('dir_name')}
    
    Tg user: {user.first_name} {user.last_name} @{user.username}
    
    Channels:
    """)


@cli.command()
@click.argument('src', nargs=-1)
@click.option('--private', is_flag=True, default=False)
@click.option('--video/--no-video', help='не выгружать видео медиа-файлы', default=True)
@click.option('--pictures/--no-pictures', help='не выгружать фотографии', default=True)
@click.option('--files/--no-files', help='не выгружать остальные типы файлов (не видео и не фотографии)',
              default=True)
@click.option('--max-size', help='максимальный размер одного выгружаемого файла в МБ', type=int)
@click.option('--update', help='обновить ранее выгруженные данные', is_flag=True, default=False)
@click.option('--format', help='формат сохранения сообщений CSV или JSON(l) формат.',
              type=click.Choice(['csv', 'json'], case_sensitive=False), default='json', show_default=True)
@click.option('--input',
              help='файл со списком названий чатов и каналов или ссылок на них если у них нет названия и они приватные.',
              type=click.File('r'))
# @click.option('--filter-text', help='фильтрация выгружаемых сообщений по через регулярное выражение по его тексту.')
@click.option('-o', '--output',
              help='путь для сохранения файлов и данных, если не задан то создается папка tgarc-<датазапуска>',
              type=click.STRING,
              )
def save(src, **kwargs):
    """сохранение группы чатов и каналов по их имени или по ссылкам"""
    dir_name = kwargs.get('output')
    if not dir_name:
        now = datetime.datetime.now()
        date_string = now.strftime('%Y%m%d_%H%M%S')
        dir_name = f'tgarc-{date_string}'
    dir_name = Path.cwd() / dir_name
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    kwargs['dir_name'] = dir_name

    input_file = kwargs.get('input')
    if input_file:
        src = []
        for line in input_file:
            src.append(line.strip())

    update_config = configparser.ConfigParser()
    update_config.read(get_update_path())
    if not update_config.has_section('message_id') or not kwargs.get('update'):
        update_config['message_id'] = dict()

    with get_pyrogram_client() as app:

        me = app.get_me()
        show_params(me, kwargs)
        if kwargs.get('private'):
            click.echo(f"Private mode\nLoading dialogs...")
            private_dialogs = filter(lambda x: x.chat.has_protected_content, app.get_dialogs())
            options = [Option(label=dialog.chat.title, value=dialog.chat.id) for dialog in private_dialogs]
            selected = pick(options, title='Select by <Space> and press <Enter>', multiselect=True, min_selection_count=1)
            src = (option[0].value for option in selected)

        for chat in src:
            try:
                chat = app.get_chat(chat)
            except ValueError:
                click.echo(f'       Wrong chat: {chat}')
            click.echo(f'       {chat.title} @{chat.username}')

            offset_id = update_config.getint('message_id', str(chat.id), fallback=None)
            new_offset_id = save_chat(app, chat, kwargs, offset_id)
            if new_offset_id:
                update_config.set('message_id', str(chat.id), str(new_offset_id))

    with open(get_update_path(), 'w') as configfile:
        update_config.write(configfile)


def download_media(app, media, dir_name, max_size):
    if not max_size or max_size * 1024 * 1024 > media.file_size:
        app.download_media(
            media.file_id,
            file_name=f'{dir_name}/{media.file_unique_id}/',
        )


def save_chat(app, chat, options=None, offset_id=None):
    if not offset_id:
        count = app.get_chat_history_count(chat.id)
        offset_id = 1
    else:
        history = list(app.get_chat_history(chat.id, limit=1))
        if not history:
            click.echo('         No messages')
            return
        count = history[0].id - offset_id
        if count <= 0:
            click.echo('         No messages')
            return

    if not options:
        options = dict()
    video = options.get('video')
    pictures = options.get('pictures')
    files = options.get('files')
    max_size = options.get('max_size')
    file_format = options.get('format')
    if file_format == 'csv':
        raise NotImplementedError()

    dir_name = f'{options["dir_name"]}/{chat.username if chat.username else chat.id}'
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    files_for_download = {
        'video': list(),
        'photo': list(),
        'files': list(),
    }
    limit = min(count, MESSAGE_LIMIT)
    with click.progressbar(length=count,
                           label='         Messages: ') as bar:
        with open(f'{dir_name}/messages.jsonl', 'w', encoding='utf-8') as f:
            history = list(app.get_chat_history(
                chat.id, offset_id=offset_id, limit=limit, offset=-limit)
            )
            while history:
                for message in reversed(history):
                    f.write(json.dumps(message, default=Object.default, ensure_ascii=False))
                    f.write('\n')
                    for media in ('video', 'photo', 'audio', 'document', 'sticker', 'animation', 'voice', 'video_note'):
                        if getattr(message, media):
                            if media in files_for_download:
                                files_for_download[media].append(getattr(message, media))
                            else:
                                files_for_download['files'].append(getattr(message, media))
                    bar.update(1)
                offset_id = message.id + 1
                history = list(app.get_chat_history(chat.id, offset_id=offset_id, limit=limit, offset=-limit))

    if video:
        with click.progressbar(files_for_download['video'],
                               label='         Videos: ') as bar:
            for media in bar:
                download_media(app, media, dir_name, max_size)
    if pictures:
        with click.progressbar(files_for_download['photo'],
                               label='         Photos: ') as bar:
            for media in bar:
                download_media(app, media, dir_name, max_size)
    if files:
        with click.progressbar(files_for_download['files'],
                               label='         Files: ') as bar:
            for media in bar:
                download_media(app, media, dir_name, max_size)
    return offset_id


@cli.command()
def logout():
    """Завершение сессии текущего пользователя"""

    with get_pyrogram_client() as app:
        app.log_out()


if __name__ == '__main__':
    cli()
