#!/bin/bash
unset LD_PRELOAD
cd /home/flomaster/warehouse-master/frontend
npx playwright test --ui-port=31323 --ui-host=0.0.0.0
