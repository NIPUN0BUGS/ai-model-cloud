# Railway RMS — Implementation Proposal

This proposal is based on the uploaded final-year project report **“Web API for Railway management system with ticket booking, train Tracking and Arrival Time Prediction.”** The report describes a web-based system for Sri Lankan railway passengers and management, with journey search, train availability/timetables, ticket reservations and cancellations, reservation references, train tracking and arrival-time prediction. It also discusses administration of railway data.

## Prototype direction
Build a responsive passenger-facing web application with journey planning, timetable discovery, a tracking/arrival-prediction view, and a demo booking flow. Clearly mark sample schedules, fares, delays and station data as illustrative until official integrations exist.

## Original report stack
The report's methodology section describes PHP with CodeIgniter, MySQL, Bootstrap, JavaScript/jQuery and AJAX. The current UI prototype can be treated as a separate frontend proof of concept; it should not be represented as the original CodeIgniter implementation.

## Required production services
- Backend API and database for users, stations, train services, scheduled stop times, seat availability, reservations, and cancellations.
- Secure authentication, role-based access, validation, password handling, audit events and abuse protection.
- Official timetable/service-status data and a GPS or operations feed for real tracking.
- Arrival-time prediction logic evaluated against real historical/observed times, with uncertainty presented honestly.
- Server-verified payments before issuing confirmed booking references.
- Tests, backups, accessibility checks, monitoring and deployment configuration.

## Prototype limitations
No backend, real database, official timetable feed, GPS tracking, prediction model, seat inventory, authentication or payment provider is connected in this proposal. Demo reservations are not valid railway tickets and are not persisted to a server.

## Reference
Source: `LMU_20048077_final project_BATCH15.pdf`, title page and Chapter 1 (Goals/Method), Problem Statement, and the report's design/implementation/testing chapters.
