import {defineConfig} from '@playwright/test';
import base from './playwright.config.mjs';
export default defineConfig({testDir:'./tests/pages',timeout:120000,workers:1,use:base.use,webServer:{command:'npm run preview -- --port 4174 --base=/yukimura/',url:'http://127.0.0.1:4174/yukimura/',reuseExistingServer:false}});
