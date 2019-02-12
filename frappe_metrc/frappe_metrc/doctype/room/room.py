# -*- coding: utf-8 -*-
# Copyright (c) 2018, Neil Lasrado and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import requests
from frappe.model.document import Document
from frappe_metrc.utils import get_metrc

metrc = get_metrc("room")

class Room(Document):
	def validate(self):
		self.create_or_update_room()
		self.check_room()
	
	def after_rename(self, old, new, merge=False):
		self.create_or_update_room()

	def create_or_update_room(self):
		data = [
			{
				"Name": self.room_name
			}
		]

		if not self.room_id:
			# Create Room in Metrc and assign ID
			room_doc = frappe.new_doc("Room")
			#room_doc.room_id = plant.get("RoomId")
			room_doc.room_name = self.room_name
			room_doc.save()
			frappe.db.commit()
			#metrc.post("/rooms/v1/create", data)
		else:
			# use the update API to update the object if room id exists
			data[0].update({"Id": self.room_id})
			metrc.post("/rooms/v1/update", data)

	def check_room(self):
		# Try to find if the room id was assigned
		rooms = metrc.get("/rooms/v1/active")
		for room in rooms:
			if room.get("Name") == self.room_name:
				self.room_id = room.get("Id")

	def on_trash(self):
		metrc.delete("/rooms/v1/" + self.room_id)
