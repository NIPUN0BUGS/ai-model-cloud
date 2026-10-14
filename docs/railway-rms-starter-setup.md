# Railway RMS starter setup

The starter application is packaged separately as `railway-rms-starter.zip` in the conversation. It uses React + Vite and provides responsive views for journey planning, sample timetables, illustrative train tracking and local demo reservations.

## Local setup
1. Extract the ZIP into a new folder such as `D:\railway-rms`.
2. In that folder run `npm install`.
3. Run `npm run dev` and open the local URL shown by Vite.
4. Run `npm run build` before deployment.

Use a current Node.js LTS supported by Vite. If npm installation fails, check network access and rerun `npm install` from the project folder.

## Reminder
This frontend is a prototype, not a connected railway booking system. All sample journeys, fares, statuses and route points are illustrative. Do not use it to sell tickets or claim real train tracking until an API/database, official service data, seat inventory, authentication and payment verification are implemented and tested.
