from django.contrib import admin

from .models import FormBlueprint, FormInstance
# Register your models here.

class FormBlueprintAdminModel(admin.ModelAdmin):
	""" Admin Model """

	list_display = ("id",  "workflow", "active", "saved")
	search_fields =("title", "workflow", )
	class Meta:
		model = FormBlueprint

admin.site.register(FormBlueprint, FormBlueprintAdminModel)

class FormInstanceAdminModel(admin.ModelAdmin):
	"""Admin model for the form instance model in forms app"""

	def blueprint_title(obj):
		return obj.blueprint.title
	blueprint_title.short_description = "BP Title"

	def blueprint_workflow(obj):
		return obj.blueprint.workflow
	blueprint_workflow.short_description = "BP Workflow"

	list_display = ("id", blueprint_title, blueprint_workflow, "current_node","sender", "active")
	search_fields = ("blueprint__title", "blueprint__workflow")
	class Meta:
		model = FormInstance

admin.site.register(FormInstance, FormInstanceAdminModel)