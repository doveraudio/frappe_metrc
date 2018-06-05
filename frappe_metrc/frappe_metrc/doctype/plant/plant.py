# -*- coding: utf-8 -*-
# Copyright (c) 2018, Neil Lasrado and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe_metrc.frappe_metrc.utils import get_metrc
metrc = get_metrc("plant")

class Plant(Document):
	def validate(self):
		# self.create_or_update_plant()
		# self.check_plant()
		self.move_plant()

	def move_plant(self):
		# if self.room != frappe.db.get_value("Plant", self.name, "room"):
		data = [{
			"Label" : self.label,
			"Room" : self.room,
			"ActualDate" : frappe.utils.today()
		}]
		metrc.post("/plants/v1/moveplants", data)

	def after_rename(self, old, new, merge=False):
		self.create_or_update_plant()

	def manicure(self):
		data = [
                    {
                        "Plant": self.label,
                        "Weight": self.weight,
                        "UnitOfWeight": self.weight_uom,
                        "DryingRoom": self.drying_room,
                        "ActualDate": frappe.utils.today()
                    }
                ]
		metrc.post("/plants/v1/manicureplants", data)

	def harvest(self):
		data = [
                    {
                        "Plant": self.label,
                        "Weight": self.weight,
                        "UnitOfWeight": self.weight_uom,
                        "DryingRoom": self.drying_room,
                        "ActualDate": frappe.utils.today(),
						"HarvestName": self.harvest_name
                    }
                ]

		if metrc.post("/plants/v1/harvestplants", data):
			harvest = frappe.new_doc("Harvest")
			harvest.harvest_name = self.harvest_name
			harvest.drying_room = self.drying_room
			harvest.save()
			frappe.db.commit()

	def create_or_update_plant(self):
		data = [
					{
						"PlantLabel": self.label,
						"PlantBatchName": self.batch,
						"PlantBatchType": self.type,
						"PlantCount": self.count,
						"StrainName": self.strain,
						"ActualDate": self.actual_date
					}
		]

		if not self.id:
			# Create Room in Metrc and assign ID
			response = metrc.post("/plants/v1/create/plantings", data)
			if response != "Success":
				frappe.throw(response)
		else:
			data[0].update({"Id": self.id})
			# use the update API to update the object if room id exists
			response = metrc.post("/plants/v1/update", data)
			if response != "Success":
				frappe.throw(response)

	def check_plant(self):
		# Try to find if the room id was assigned
		plant = metrc.get("/plants/v1/{}".format(self.label))
		if not plant:
			return

		self.id = plant.get("Id")
		self.type = plant.get("PlantBatchType")
		self.count = plant.get("PlantCount")
		self.actual_date = plant.get("ActualDate")
		self.state = plant.get("State")
		self.growth_phase = plant.get("GrowthPhase")

		if not frappe.db.exists("Plant Batch", plant.get("PlantBatchName")):
			plant_batch_doc = frappe.new_doc("Plant Batch")
			plant_batch_doc.batch_id = plant.get("PlantBatchId")
			plant_batch_doc.type = plant.get("PlantBatchType")
			plant_batch_doc.batch_name = plant.get("PlantBatchName")
			plant_batch_doc.save()
			frappe.db.commit()


		if not frappe.db.exists("Room", plant.get("RoomName")):
			room_doc = frappe.new_doc("Room")
			room_doc.room_id = plant.get("RoomId")
			room_doc.room_name = plant.get("RoomName")
			room_doc.save()
			frappe.db.commit()


		if not frappe.db.exists("Strain", plant.get("StrainName")):
			room_doc = frappe.new_doc("Strain")
			room_doc.strain_id = plant.get("StrainId")
			room_doc.strain_name = plant.get("StrainName")
			room_doc.save()
			frappe.db.commit()

		self.batch = plant.get("PlantBatchName")
		self.strain = plant.get("StrainName")
		self.room = plant.get("RoomName")


	def on_trash(self):
		data = [{
			"Label": self.label,
			"ActualDate": frappe.utils.today(),
			"ReasonNote": "Just Cause"
		}]
		metrc.post("/plants/v1/destroyplants", data)