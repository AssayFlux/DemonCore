"""DCP v1 codec, routing and error replies.
Heap: bounded by 4 KiB input, 64 members/container and depth 8; no persistent buffers.
RAM: run firmware/tests/measure_dcp_ram.py on the target MicroPython runtime.
"""
try:
    import ujson as json
except ImportError:
    import json

VERSION = "1.0"
MAX_MESSAGE_BYTES = 4096
MAX_DEPTH = 8
MAX_MEMBERS = 64
ERROR_CODES = (
    "E_BAD_MESSAGE", "E_VERSION", "E_NOT_FOUND", "E_UNSUPPORTED",
    "E_INVALID_ARG", "E_DENIED", "E_PIN_BLOCKED", "E_CONFIRM_REQUIRED",
    "E_BUSY", "E_TIMEOUT", "E_TOO_LARGE", "E_INTERNAL",
)
_OPERATIONS = ("sys.info", "sys.ping", "gpio.mode", "gpio.read", "gpio.write")
_MODES = ("input", "input_pullup", "input_pulldown", "output")


class DCPError(Exception):
    def __init__(self, code, message, details=None):
        self.code = code
        self.message = str(message)[:160]
        self.details = details

    def __str__(self):
        return self.message


def _fail(code, message):
    raise DCPError(code, message)


def _skip_ws(source, index):
    while index < len(source) and source[index] in " \t\r\n":
        index += 1
    return index


def _scan_string(source, index):
    start = index
    index += 1
    while index < len(source):
        char = source[index]
        if char == '"':
            token = source[start:index + 1]
            try:
                return json.loads(token), index + 1
            except Exception:
                _fail("E_BAD_MESSAGE", "Invalid JSON string")
        if ord(char) < 32:
            _fail("E_BAD_MESSAGE", "Control character in JSON string")
        if char == "\\":
            index += 1
            if index >= len(source):
                break
            escaped = source[index]
            if escaped == "u":
                if index + 4 >= len(source):
                    break
                for digit in source[index + 1:index + 5]:
                    if digit not in "0123456789abcdefABCDEF":
                        _fail("E_BAD_MESSAGE", "Invalid Unicode escape")
                index += 4
            elif escaped not in '"\\/bfnrt':
                _fail("E_BAD_MESSAGE", "Invalid JSON escape")
        index += 1
    _fail("E_BAD_MESSAGE", "Unterminated JSON string")


def _valid_number(token):
    if not token:
        return False
    index = 1 if token[0] == "-" else 0
    if index >= len(token):
        return False
    if token[index] == "0":
        index += 1
        if index < len(token) and token[index].isdigit():
            return False
    elif "1" <= token[index] <= "9":
        while index < len(token) and token[index].isdigit():
            index += 1
    else:
        return False
    if index < len(token) and token[index] == ".":
        index += 1
        start = index
        while index < len(token) and token[index].isdigit():
            index += 1
        if index == start:
            return False
    if index < len(token) and token[index] in "eE":
        index += 1
        if index < len(token) and token[index] in "+-":
            index += 1
        start = index
        while index < len(token) and token[index].isdigit():
            index += 1
        if index == start:
            return False
    return index == len(token)


def _scan_value(source, index, depth):
    index = _skip_ws(source, index)
    if index >= len(source):
        _fail("E_BAD_MESSAGE", "Unexpected end of JSON")
    char = source[index]
    if char == '"':
        unused, index = _scan_string(source, index)
        return index
    if char == "{":
        if depth > MAX_DEPTH + 2:
            _fail("E_TOO_LARGE", "JSON nesting limit exceeded")
        index = _skip_ws(source, index + 1)
        keys = []
        count = 0
        if index < len(source) and source[index] == "}":
            return index + 1
        while True:
            if index >= len(source) or source[index] != '"':
                _fail("E_BAD_MESSAGE", "Object key must be a string")
            key, index = _scan_string(source, index)
            if key in keys:
                _fail("E_BAD_MESSAGE", "Duplicate JSON object key")
            keys.append(key)
            count += 1
            if count > MAX_MEMBERS:
                _fail("E_TOO_LARGE", "JSON object member limit exceeded")
            index = _skip_ws(source, index)
            if index >= len(source) or source[index] != ":":
                _fail("E_BAD_MESSAGE", "Missing object colon")
            index = _scan_value(source, index + 1, depth + 1)
            index = _skip_ws(source, index)
            if index < len(source) and source[index] == "}":
                return index + 1
            if index >= len(source) or source[index] != ",":
                _fail("E_BAD_MESSAGE", "Missing object comma")
            index = _skip_ws(source, index + 1)
    if char == "[":
        if depth > MAX_DEPTH + 2:
            _fail("E_TOO_LARGE", "JSON nesting limit exceeded")
        index = _skip_ws(source, index + 1)
        count = 0
        if index < len(source) and source[index] == "]":
            return index + 1
        while True:
            count += 1
            if count > MAX_MEMBERS:
                _fail("E_TOO_LARGE", "JSON array member limit exceeded")
            index = _scan_value(source, index, depth + 1)
            index = _skip_ws(source, index)
            if index < len(source) and source[index] == "]":
                return index + 1
            if index >= len(source) or source[index] != ",":
                _fail("E_BAD_MESSAGE", "Missing array comma")
            index = _skip_ws(source, index + 1)
    end = index
    while end < len(source) and source[end] not in ",]} \t\r\n":
        end += 1
    token = source[index:end]
    if token in ("true", "false", "null"):
        return end
    if not _valid_number(token):
        _fail("E_BAD_MESSAGE", "Invalid JSON value")
    return end


def _check_tree(value, depth=0):
    if isinstance(value, dict):
        if depth > MAX_DEPTH or len(value) > MAX_MEMBERS:
            _fail("E_TOO_LARGE", "DCP args nesting or member limit exceeded")
        for child in value.values():
            _check_tree(child, depth + 1)
    elif isinstance(value, list):
        if depth > MAX_DEPTH or len(value) > MAX_MEMBERS:
            _fail("E_TOO_LARGE", "DCP args nesting or member limit exceeded")
        for child in value:
            _check_tree(child, depth + 1)
    elif isinstance(value, float):
        if value != value or value == float("inf") or value == -float("inf"):
            _fail("E_BAD_MESSAGE", "Non-finite JSON number")


def _slug(value):
    if not isinstance(value, str) or len(value) < 1 or len(value) > 32:
        return False
    if value[0] < "a" or value[0] > "z":
        return False
    for char in value[1:]:
        if not (("a" <= char <= "z") or ("0" <= char <= "9") or char in "_-"):
            return False
    return True


def _address(value, source=False):
    if not isinstance(value, str):
        return False
    if value == "*":
        return not source
    if value.startswith("node:"):
        number = value[5:]
        if not number or len(number) > 20 or number[0] < "1" or number[0] > "9":
            return False
        for digit in number[1:]:
            if digit < "0" or digit > "9":
                return False
        return True
    for prefix in ("group:", "tag:", "cell:"):
        if value.startswith(prefix):
            return (not source) and _slug(value[len(prefix):])
    return False


def _keys(args, allowed, required=()):
    if not isinstance(args, dict):
        _fail("E_INVALID_ARG", "Operation args must be an object")
    for key in required:
        if key not in args:
            _fail("E_INVALID_ARG", "Missing argument: " + key)
    for key in args:
        if key not in allowed:
            _fail("E_INVALID_ARG", "Unexpected argument: " + str(key))


def _integer(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail("E_INVALID_ARG", "Invalid integer argument: " + name)
    if maximum is not None and value > maximum:
        _fail("E_INVALID_ARG", "Integer argument out of range: " + name)


def _string(value, name, limit):
    if not isinstance(value, str) or len(value) > limit:
        _fail("E_INVALID_ARG", "Invalid string argument: " + name)


def _validate_operation(message):
    op = message["op"]
    kind = message["t"]
    args = message["args"]
    if op not in _OPERATIONS:
        _fail("E_UNSUPPORTED", "Unsupported DCP operation")
    if kind == "evt":
        return
    if kind == "res" and "error" in args:
        _keys(args, ("error",), ("error",))
        error = args["error"]
        if not isinstance(error, dict) or error.get("code") not in ERROR_CODES:
            _fail("E_INVALID_ARG", "Invalid error response")
        _keys(error, ("code", "message", "details"), ("code", "message"))
        _string(error["message"], "error.message", 160)
        if "details" in error and not isinstance(error["details"], dict):
            _fail("E_INVALID_ARG", "error.details must be an object")
        return
    if op == "sys.info":
        if kind == "req":
            _keys(args, ())
        else:
            _keys(args, ("firmware", "hardware", "capabilities"),
                  ("firmware", "hardware", "capabilities"))
            _string(args["firmware"], "firmware", 64)
            _string(args["hardware"], "hardware", 64)
            caps = args["capabilities"]
            if not isinstance(caps, list) or len(caps) > 64:
                _fail("E_INVALID_ARG", "Invalid capabilities")
            for item in caps:
                _string(item, "capability", 64)
    elif op == "sys.ping":
        if kind == "req":
            _keys(args, ("token",))
            if "token" in args:
                _string(args["token"], "token", 64)
        else:
            _keys(args, ("uptime_ms", "token"), ("uptime_ms",))
            _integer(args["uptime_ms"], "uptime_ms")
            if "token" in args:
                _string(args["token"], "token", 64)
    elif op == "gpio.mode":
        if kind == "req":
            _keys(args, ("pin", "mode", "confirm"), ("pin", "mode"))
            _integer(args["pin"], "pin", 0, 39)
            if args["mode"] not in _MODES:
                _fail("E_INVALID_ARG", "Invalid GPIO mode")
            if "confirm" in args and not isinstance(args["confirm"], bool):
                _fail("E_INVALID_ARG", "confirm must be boolean")
        else:
            _keys(args, ("pin", "mode"), ("pin", "mode"))
            _integer(args["pin"], "pin", 0, 39)
            if args["mode"] not in _MODES:
                _fail("E_INVALID_ARG", "Invalid GPIO mode")
    elif op == "gpio.read":
        if kind == "req":
            _keys(args, ("pin",), ("pin",))
            _integer(args["pin"], "pin", 0, 39)
        else:
            _keys(args, ("pin", "value"), ("pin", "value"))
            _integer(args["pin"], "pin", 0, 39)
            _integer(args["value"], "value", 0, 1)
    elif op == "gpio.write":
        if kind == "req":
            _keys(args, ("pin", "value", "confirm"), ("pin", "value"))
            _integer(args["pin"], "pin", 0, 39)
            _integer(args["value"], "value", 0, 1)
            if "confirm" in args and not isinstance(args["confirm"], bool):
                _fail("E_INVALID_ARG", "confirm must be boolean")
        else:
            _keys(args, ("pin", "value"), ("pin", "value"))
            _integer(args["pin"], "pin", 0, 39)
            _integer(args["value"], "value", 0, 1)


def validate(message):
    if not isinstance(message, dict):
        _fail("E_BAD_MESSAGE", "DCP message must be an object")
    expected = ("v", "id", "src", "dst", "t", "op", "args")
    _keys(message, expected, expected)
    if message["v"] != VERSION:
        _fail("E_VERSION", "Unsupported DCP version")
    identifier = message["id"]
    if not isinstance(identifier, str) or len(identifier) < 16 or len(identifier) > 32:
        _fail("E_BAD_MESSAGE", "Invalid message identifier")
    for digit in identifier:
        if not (("0" <= digit <= "9") or ("a" <= digit <= "f")):
            _fail("E_BAD_MESSAGE", "Invalid message identifier")
    if not _address(message["src"], True) or not message["src"].startswith("node:"):
        _fail("E_BAD_MESSAGE", "Invalid source address")
    if not _address(message["dst"]):
        _fail("E_BAD_MESSAGE", "Invalid destination address")
    if message["t"] not in ("req", "res", "evt"):
        _fail("E_BAD_MESSAGE", "Invalid message type")
    op = message["op"]
    if not isinstance(op, str) or len(op) > 64:
        _fail("E_BAD_MESSAGE", "Invalid operation name")
    parts = op.split(".")
    if len(parts) < 2:
        _fail("E_BAD_MESSAGE", "Invalid operation name")
    for part in parts:
        if not part or part[0] < "a" or part[0] > "z":
            _fail("E_BAD_MESSAGE", "Invalid operation name")
        for char in part[1:]:
            if not (("a" <= char <= "z") or ("0" <= char <= "9") or char == "_"):
                _fail("E_BAD_MESSAGE", "Invalid operation name")
    if not isinstance(message["args"], dict):
        _fail("E_BAD_MESSAGE", "DCP args must be an object")
    _check_tree(message["args"])
    _validate_operation(message)
    return message


def decode(payload):
    if isinstance(payload, bytes):
        raw = payload
        try:
            source = payload.decode("utf-8")
        except Exception:
            _fail("E_BAD_MESSAGE", "Invalid UTF-8")
    elif isinstance(payload, str):
        source = payload
        raw = source.encode("utf-8")
    else:
        _fail("E_BAD_MESSAGE", "DCP payload must be bytes or text")
    if len(raw) > MAX_MESSAGE_BYTES:
        _fail("E_TOO_LARGE", "DCP message exceeds 4096 bytes")
    end = _scan_value(source, 0, 0)
    if _skip_ws(source, end) != len(source):
        _fail("E_BAD_MESSAGE", "Trailing data after JSON message")
    try:
        message = json.loads(source)
    except Exception:
        _fail("E_BAD_MESSAGE", "Malformed JSON")
    return validate(message)


def encode(message):
    validate(message)
    try:
        payload = json.dumps(message)
    except Exception:
        _fail("E_BAD_MESSAGE", "DCP message cannot be encoded")
    if isinstance(payload, bytes):
        raw = payload
    else:
        raw = payload.encode("utf-8")
    if len(raw) > MAX_MESSAGE_BYTES:
        _fail("E_TOO_LARGE", "DCP message exceeds 4096 bytes")
    decode(raw)
    return raw


def matches_destination(destination, node_id, groups=None, tags=None, cells=None):
    if isinstance(node_id, int) and not isinstance(node_id, bool):
        node_address = "node:" + str(node_id)
    else:
        node_address = str(node_id)
        if not node_address.startswith("node:"):
            node_address = "node:" + node_address
    if destination == "*":
        return True
    if destination == node_address:
        return True
    if not isinstance(destination, str) or ":" not in destination:
        return False
    prefix, selector = destination.split(":", 1)
    values = groups if prefix == "group" else tags if prefix == "tag" else cells if prefix == "cell" else ()
    return selector in (values or ())


def route(message, node_id, groups=None, tags=None, cells=None):
    validate(message)
    return matches_destination(message["dst"], node_id, groups, tags, cells)


def make_error_reply(request, code, message, details=None, responder=None):
    if code not in ERROR_CODES:
        code = "E_INTERNAL"
    args = {"error": {"code": code, "message": str(message)[:160]}}
    if details is not None:
        if not isinstance(details, dict):
            _fail("E_INVALID_ARG", "Error details must be an object")
        args["error"]["details"] = details
    source = responder if responder is not None else request["dst"]
    if not isinstance(source, str) or not source.startswith("node:"):
        _fail("E_INVALID_ARG", "A concrete responder node address is required")
    reply = {
        "v": VERSION, "id": request["id"], "src": source,
        "dst": request["src"], "t": "res", "op": request["op"], "args": args,
    }
    return validate(reply)
