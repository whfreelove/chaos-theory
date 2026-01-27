#!/usr/bin/env bash
next_gap=$(grep -oE 'GAP-[0-9]+' ${1}/gaps.md ${1}/resolved.md 2>/dev/null | grep -oE '[0-9]+' | sort -n | tail -1)
echo "Next available: GAP-$((${next_gap:-0} + 1))"
