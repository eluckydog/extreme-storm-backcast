#!/usr/bin/env python3
"""Carrington Space Engine — Agent CLI Entry Point.

Usage:
    python -m carrington --report         # Print Carrington summary
    python -m carrington --report 1989    # Report a specific event (event name/year)
    python -m carrington --sweep          # Run parameter sweep
    python -m carrington --events         # List all calibrated events
    python -m carrington --calibrate      # Cross-calibrate all events
    python -m carrington --interactive    # Interactive query mode
"""

import sys, os

def print_summary():
    print("=" * 60)
    print("  CARRINGTON SPACE ENGINE v1.0.0")
    print("  Self-consistent Dst evolution model")
    print("=" * 60)
    print()
    print("  Core finding: Carrington Dst ≈ −774 nT (not −1600 nT)")
    print()
    print("  Key references:")
    print("    Beggan+ 2024 (BGS digitised magnetograms)")
    print("    Hayakawa+ 2019 (1859 event review)")
    print("    Siscoe 2006 (Dst saturation)")
    print("    Cliver 2013 (1859 revisit)")
    print()
    print("  Available events (9 calibrated):")
    print("    1859, 1986, 1989, 2000, 2003,")
    print("    2004, 2015, 2024, 2024-05")
    print()
    print("  Commands:")
    print("    python -m carrington --report <event>")
    print("    python -m carrington --events")
    print("    python -m carrington --sweep")
    print("    python -m carrington --interactive")

def print_events():
    from .event_params import EVENT_PARAMS
    print(f"{'Event':20s} {'Dst obs':>8s} {'Dst v2':>8s} {'Bz':>6s} {'Vsw':>6s} {'Notes'}")
    print("-" * 60)
    for name, p in EVENT_PARAMS.items():
        dst_o = f"{p['dst_observed']:.0f}" if p.get('dst_observed') else "  N/A"
        dst_v = f"{p['dst_v2']:.0f}" if p.get('dst_v2') else "  N/A"
        bz = f"{p['bz']:.0f}" if p.get('bz') else "?"
        vsw = f"{p['v_sw']:.0f}" if p.get('v_sw') else "?"
        note = p.get('note', '')[:30]
        print(f"  {name:20s} {dst_o:>8s} {dst_v:>8s} {bz:>6s} {vsw:>6s} {note}")

def print_event(name):
    from .event_params import EVENT_PARAMS
    p = EVENT_PARAMS.get(name)
    if not p:
        # Try partial match
        matches = [k for k in EVENT_PARAMS if name.lower() in k.lower()]
        if matches:
            for m in matches[:5]:
                print(f"  Did you mean: {m}")
        else:
            print(f"  Event '{name}' not found.")
        return
    print(f"\n  === {name} ===")
    for k, v in p.items():
        print(f"    {k}: {v}")

def interactive():
    print("\n  Interactive mode (type 'exit' to quit, 'help' for commands)\n")
    while True:
        try:
            cmd = input("  carrington> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not cmd:
            continue
        if cmd in ("exit", "quit", "q"):
            break
        if cmd in ("help", "?"):
            print("  Commands: report, events, sweep, exit")
            continue
        if cmd == "report":
            print_summary()
        elif cmd == "events":
            print_events()
        elif cmd.startswith("report "):
            print_event(cmd[7:].strip())
        elif cmd.startswith("sweep"):
            print("  Run: python scripts/_carrington_sweep.py")
        else:
            print(f"  Unknown: {cmd}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_summary()
        return
    cmd = sys.argv[1]
    if cmd == "--report":
        if len(sys.argv) > 2:
            print_event(sys.argv[2])
        else:
            print_summary()
    elif cmd == "--events":
        print_events()
    elif cmd == "--sweep":
        print("  Run: python scripts/_carrington_sweep.py")
    elif cmd == "--calibrate":
        from .cross_calibrate import CrossCalibrator
        from .event_params import EVENT_PARAMS
        cc = CrossCalibrator(EVENT_PARAMS)
        cc.run()
    elif cmd in ("-i", "--interactive"):
        interactive()
    else:
        print(f"  Unknown command: {cmd}")

if __name__ == "__main__":
    main()
