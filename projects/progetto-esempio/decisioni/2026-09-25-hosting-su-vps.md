---
title: "Hosting del bot su VPS invece che serverless"
summary: "ESEMPIO: il bot del progetto esempio gira su un VPS perché serve un processo sempre attivo per l'invio mattutino. Da cancellare."
type: decision
status: active
tags: [decisione, esempio]
related: ["[[projects/progetto-esempio/stato]]"]
date: 2026-09-25
project: "progetto-esempio"
updated: 2026-09-25
---
# Hosting del bot su VPS invece che serverless

## Contesto
Il bot gira solo in locale e non c'è un ambiente di produzione. Deve inviare un promemoria ogni mattina.

## Opzioni considerate
1. **VPS** — pro: processo sempre attivo, scheduler interno, costo fisso basso / contro: aggiornamenti e sicurezza del server a mio carico.
2. **Piattaforma serverless** — pro: nessun server da gestire / contro: serve uno scheduler esterno, limiti di durata delle esecuzioni.

## Decisione
Il bot va su un VPS.

## Motivazione
L'invio mattutino richiede un processo sempre attivo; con un VPS lo scheduling resta nel codice e il costo è prevedibile.

## Conseguenze
Serve uno script di deploy e una routine di aggiornamento del server. Da rivedere se i volumi crescono.
