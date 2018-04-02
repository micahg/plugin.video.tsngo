import requests, json
from utils import log
from datetime import datetime, timedelta
from dateutil.parser import *
from dateutil.tz import *

class Schedule:
    CHANNEL_PREFIX = 'tsn'
    TIME_FMT = '%Y-%m-%dT%H:%M:%S%z'
    DATE_FMT = '%Y-%m-%d'
    SCHEDULE_URL = 'https://capi.9c9media.com/destinations/tsn_web/platforms/desktop/channelAffiliates/{}-g/schedules?StartTime={}&EndTime={}'

    @staticmethod
    def getSchedule(ts, channel):
        if not channel[0:3].lower() == Schedule.CHANNEL_PREFIX:
            return []

        now_str = ts.strftime(Schedule.DATE_FMT)
        tmr_str = (ts + timedelta(days=1)).strftime(Schedule.DATE_FMT)
        url = Schedule.SCHEDULE_URL.format(channel.lower(), now_str, tmr_str)
        r = requests.get(url)
        if not r.status_code == 200:
            log('Unable to retrieve schedule for "{}"'.format(channel), True)
            return None

        return json.loads(r.content)['Items']

    @staticmethod
    def getCurrentProgram(channel):
        now = datetime.now(tzlocal())
        items = Schedule.getSchedule(now, channel)
        for item in items:
            start = parse(item['StartTime'])
            end = parse(item['EndTime'])
            if now > start and now < end:
                return item
        return {}