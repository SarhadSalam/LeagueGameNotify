# json fallback
def toJson(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__

class ColorCodes():
    GREEN = "diff\n+ "
    YELLOW = "fix"
    RED = "diff\n- "
