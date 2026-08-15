"""Second entrypoint: print a plain-text tank report to stdout."""
from config import load_config
from services import tank_summary
from models import Tank
from utils import is_alert_temp


def main():
    cfg = load_config()
    print("tidepool tank report")
    print("=" * 40)
    for name in cfg["tank_names"]:
        s = tank_summary(Tank(name))
        flag = " ALERT" if is_alert_temp(s["mean_temp_c"]) else ""
        print(f"{s['tank']:<14} {s['samples']:>4} samples  "
              f"mean {s['mean_temp_c']}C{flag}")


if __name__ == "__main__":
    main()
