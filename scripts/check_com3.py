import traceback
import sys
import importlib.util
from types import ModuleType

# Load elm327_adapter module directly from file to avoid package import issues
spec = importlib.util.spec_from_file_location('elm327_adapter', r'C:\Users\gromu\IdeaProjects\obd\elm327_diagnostic\elm327_adapter.py')
elm327_adapter = importlib.util.module_from_spec(spec)  # type: ModuleType
sys.modules['elm327_adapter'] = elm327_adapter
spec.loader.exec_module(elm327_adapter)
ELM327Adapter = elm327_adapter.ELM327Adapter

PORT = 'COM3'

def safe_call(fn, name):
    try:
        return fn()
    except Exception as e:
        print(f"{name} exception: {e}")
        traceback.print_exc()
        return None

if __name__ == '__main__':
    print(f"Running COM checks for port: {PORT}")
    adapter = ELM327Adapter(PORT)
    print('Traffic log file:', adapter.get_traffic_log_file())

    ok = safe_call(lambda: adapter.connect(), 'connect')
    print('connect result:', ok)

    v = safe_call(lambda: adapter.get_voltage(), 'get_voltage')
    print('ECU voltage:', v)

    v5 = safe_call(lambda: adapter.get_5v_reference(), 'get_5v_reference')
    print('5V reference:', v5)

    proto = safe_call(lambda: adapter._get_protocol(), '_get_protocol')
    print('protocol:', proto)

    pid = safe_call(lambda: adapter.send_obd_command('0100'), 'send_obd_command(0100)')
    print('0100 response:', pid)

    # Disconnect if connected
    try:
        if adapter.serial_conn and adapter.serial_conn.is_open:
            adapter.disconnect()
            print('Disconnected')
    except Exception:
        pass
