import json
import logging
import os

from dotenv import load_dotenv
from fastapi import Request
import aiohttp as aiohttp

from db.schemas import UserCreate

load_dotenv()

logger = logging.getLogger('app.services.user_verification')


async def clearbit_new_user_score_checker(user_data: UserCreate, request: Request) -> str:
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
    url = os.getenv('HUNTER_URL')
    api_key = os.getenv('HUNTER_API_KEY')
    params = {'email': user_data.email, 'api_key': api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                hunter_data = await resp.text()
                clean_data = json.loads(hunter_data)
                if clean_data['errors']:
                    return 'Invalid email'

                hunter_user_email_score = clean_data['data']['status']
                if hunter_user_email_score in ['invalid', 'unknown']:
                    return 'Invalid email'

        except aiohttp.ClientConnectorError as err:
            logger.exception(err)
