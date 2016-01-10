from datetime import datetime, date


def date_from_ldap_timestamp(timestamp):
    """
    Takes an LDAP date (In the form YYYYmmdd with whatever is after that) and returns a datetime.date object.
    :param timestamp: LDAP date to convert
    :return: datetime.date object
    """
    # Only check the first 8 characters: YYYYmmdd
    number_of_characters = len("YYYYmmdd")
    timestamp = timestamp[:number_of_characters]

    try:
        day = datetime.strptime(timestamp, '%Y%m%d')
        return date(year=day.year, month=day.month, day=day.day)
    except:
        return None
