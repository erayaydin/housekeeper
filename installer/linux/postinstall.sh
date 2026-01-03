#!/bin/sh
systemctl daemon-reload
echo "Housekeeper installed. To enable the service, run:"
echo "  sudo systemctl enable --now housekeeper"