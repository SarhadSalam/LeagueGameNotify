# json fallback
def toJson(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__
