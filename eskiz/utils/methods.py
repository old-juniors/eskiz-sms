class Methods:
    """
    List of API methods

    https://documenter.getpostman.com/view/663428/RzfmES4z
    """

    # AUTHORIZATION
    GET_TOKEN = {"method": "POST", "path": "auth/login"}
    REFRESH_TOKEN = {"method": "PATCH", "path": "auth/refresh"}
    GET_USER_DATA = {"method": "GET", "path": "auth/user"}

    # TEMPLATES
    GET_TEMPLATE = {"method": "GET", "path": "template/{id}"}
    GET_TEMPLATE_LIST = {"method": "GET", "path": "templates/"}

    # SENDING
    SEND_SMS = {"method": "POST", "path": "message/sms/send"}
    SEND_BATCH_SMS = {"method": "POST", "path": "message/sms/send-batch"}
    SEND_INTERNATIONAL_SMS = {
        "method": "POST",
        "path": "message/sms/send-global",
    }
    GET_MESSAGE_DETAILS = {
        "method": "POST",
        "path": "message/sms/get-user-messages",
    }
    GET_MESSAGE_BY_DISPATCH = {
        "method": "POST",
        "path": "message/sms/get-user-messages-by-dispatch",
    }
    GET_DISPATCH_STATUS = {
        "method": "POST",
        "path": "message/sms/get-dispatch-status",
    }
    GET_NICK_LIST = {"method": "GET", "path": "nick/me"}

    # REPORTS
    GET_SMS_TOTALS = {"method": "POST", "path": "user/totals"}
    GET_LIMIT = {"method": "GET", "path": "user/get-limit"}
