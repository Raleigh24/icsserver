#!/usr/bin/env bash


echo "Starting ICS server"
icsstart

sleep 5

echo "Creating basic group"
./setup_basic_group.sh

sleep 5

echo "Bringing group online"
icsgrp -online group-a

sleep 20

echo "Bringing group offline"
icsgrp -offline group-a

sleep 20


echo "Stopping ICS server"
icsstop

