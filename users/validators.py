import json
import logging
import os

from dotenv import load_dotenv
from fastapi import Request
import aiohttp as aiohttp

from users.schemas import UserCreate

load_dotenv()

logger = logging.getLogger('app.services.validators')


async def clearbit_new_user_score_checker(user_data: UserCreate, request: Request) -> str:
    """Возвращает риск score от clearbit на основе указанного пользователем емейла и его айпи"""
    url = os.getenv('CLEARBIT_URL')
    api_key = os.getenv('CLEARBIT_API_KEY')
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {'email': user_data.email,
              'ip': request.client.host}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=params, headers=headers) as resp:
                clearbit_data = await resp.text()
                clean_data = json.loads(clearbit_data)
                clearbit_user_risk_level = clean_data['risk']['level']
                return clearbit_user_risk_level
        except aiohttp.ClientConnectorError as err:
            logger.exception(err)


async def hunter_user_email_checker(user_data: UserCreate) -> str:
    """Возвращает ответ если указанный при регистрации емейл невалидный на основе проверки сервиса Hunter.io"""
    url = os.getenv('HUNTER_URL')
    api_key = os.getenv('HUNTER_API_KEY')
    params = {'email': user_data.email, 'api_key': api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                hunter_data = await resp.text()
                clean_data = json.loads(hunter_data)
                email_validation_error = clean_data.get('errors')
                if email_validation_error:
                    return 'Invalid email'
                else:
                    hunter_user_email_score = clean_data['data']['status']
                    if hunter_user_email_score in ['invalid', 'unknown']:
                        return 'Invalid email'

        except aiohttp.ClientConnectorError as err:
            logger.exception(err)
