#!/bin/sh
systemctl stop housekeeper 2>/dev/null || true
systemctl disable housekeeper 2>/dev/null || true