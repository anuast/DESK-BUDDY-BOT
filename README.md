# Desk Buddy Bot 

A cross-language, multi-threaded productivity agent that monitors both digital activity and physical presence to mitigate study procrastination in real-time.

## System Architecture & Engineering Concepts
- Polyglot Framework Integration: Built an inter-process communication (IPC) channel passing live telemetry metadata strings across runtime execution environments from Python to a compiled C++ machine binary via argument vectors (argc/argv).
- Asynchronous Concurrency Management: Deployed a multi-threaded system structure (threading) to split workload operations. The system runs real-time computer vision frame loops and OS window hooks concurrently without causing memory thrashing or processing bottlenecks.
- Native OS Subsystem Communication: Utilized low-level system hooks to read focused active process labels via window handles, and invoked native Windows shell objects to parse compressed audio layers with high efficiency.
- Throttled Hardware Polling Pattern: Optimized background computation loops down to <1% CPU utilization by implementing throttled evaluation sleep vectors, protecting primary system resources.

## Repository Directory Elements
- main.py — Orchestrates thread lifecycles and launches telemetry loops.
- boss.py — Monitors active operating system window headers for targeted platform blocks (e.g., Pinterest, YouTube).
- vision_sensor.py — Captures real-time camera frames and applies OpenCV geometric checks to audit user focus boundaries.
- worker.cpp — Low-overhead compilation driver that targets system media frameworks to fire custom audio notes instantly.
- whatsapp_converter.py — Decodes cellular compression codecs into uncompressed desktop formats.
