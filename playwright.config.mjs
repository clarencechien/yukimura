import { defineConfig } from '@playwright/test';
import {existsSync} from 'node:fs';
export default defineConfig({testDir:'./tests/browser',timeout:120000,workers:1,use:{headless:true,launchOptions:{executablePath:process.env.CHROMIUM_PATH||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']}},webServer:[{command:'npm run dev -- --port 5175',url:'http://127.0.0.1:5175',reuseExistingServer:false},{command:'npm run preview -- --port 4173',url:'http://127.0.0.1:4173',reuseExistingServer:false}]});
