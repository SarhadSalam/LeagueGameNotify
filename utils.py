# json fallback
def toJson(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__

class ColorCodes():
    GREEN = "```diff\n+ {msg}\n```"
    YELLOW = "```fix\n{msg}\n```"
    RED = "```diff\n- {msg}\n```"

def applyColorToMsg(msg, color):
    if color is None:
        return msg
    return color.format(msg=msg)
