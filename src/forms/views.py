from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
import json
import pymongo
from pymongo import MongoClient
from django.conf import settings
import datetime
import pytz

from .forms import FormBlueprintForm
from .models import FormBlueprint, FormInstance, FormNotification, FormInstanceHasComment, TeamHasBlueprintPersmission
from employees.models import Profile
from workflows.models import Workflow, Node
from teams.models import TeamHasEmployees
from django.http import JsonResponse
from .routing import get_node_user

from django.db import transaction



# Create your views here.
@login_required
def dashboard(request):
    #separate the form instances into two parts....those that I have seen in the past and those that are now pending with me

    try:
        user_profile = request.user.profile
        the_instance = user_profile.teamhasemployees

        notifications = FormNotification.objects.filter(user = the_instance, form_instance__active = True, status = 'N').order_by('id')


        forms_no_action = [(n.form_instance, n.form_instance.is_user_current_node(user_profile)) for n in notifications]
        fi_no_action = [i[0] for i in forms_no_action] 
        rest_form_instances=[fi for fi in FormInstance.objects.all() if fi not in fi_no_action]
        # final_list=[]
        # for form, cn in forms_no_action:
        #     for notification in notifications:
        #         if notification.form_instance==form and notification.status=='N':
        #             final_list.append((form,cn))
        #         elif notification.form_instance==form:
        #             break

        # user_role=the_instance.role
        # user_team=the_instance.team
        # form_list_pending_with_me=[]
        # for form in FormInstance.objects.all():
        #     if (form.current_node.associated_role==user_role  and form.current_node.associated_team==user_team):
        #         form_list_pending_with_me.append(form)

        #could further divide into active and inactive
        context = {
            'pending_with_me_form_instances': forms_no_action,
            'rest_form_instances': rest_form_instances,
        }
        return render(request, 'forms/dashboard.html', context=context)
    except Exception as e:
        print("in dashboard: "+str(e))
        return render(request, 'message.html', {'message': "You haven't been assigned a team yet"})

@login_required
def send_comment(request):
    user_profile = request.user.profile
    the_sender = user_profile.teamhasemployees

    try:
        if request.method == 'POST':
            fi = int(request.POST.get('fi_id'))
            form_instance = FormInstance.objects.get(pk = fi)
            receiver_id = int(request.POST.get('receiver'))
            receiver = Profile.objects.get(pk = receiver_id)
            the_receiver = TeamHasEmployees.objects.get(employee__id = receiver_id)

            comment = request.POST.get('comment')
        
            fn_sender = FormNotification.objects.get(user = the_sender, form_instance = form_instance)
            print(fn_sender)
            fn_sender.status = 'B'
            fn_sender.save()

            fn_receiver = FormNotification.objects.get(user = the_receiver, form_instance = form_instance)
            print(fn_receiver)
            fn_receiver.status = 'N'
            fn_receiver.save()

            form_blueprint = form_instance.blueprint
            workflow = form_blueprint.workflow

            curr_node = Node.objects.get(workflow = workflow, prev_node = None)

            while (get_node_user(curr_node, form_instance.sender) != receiver) & (curr_node.next_node != None):
                curr_node = curr_node.next_node

            form_instance.current_node = curr_node
            form_instance.save()

            comment_instance = FormInstanceHasComment(form_instance = form_instance, sender = user_profile, receiver = receiver , comment = comment)
            comment_instance.save()
            context={
                            'message': "Successful"
                        }
            return render(request, 'forms/redirect_to_dashboard.html', context = context)
            
    except Exception as e:
        print(e)
        context={
                            'message': "Failed"
                        }
        return render(request, 'forms/redirect_to_dashboard.html', context = context)

@login_required
def fb_all(request):
    #check if the team of the user is present in TeamHasBlueprintPermissions
    user_team=TeamHasEmployees.objects.get(employee=request.user.profile).team
    try:
        check=TeamHasBlueprintPersmission.objects.get(team = user_team)
        if(check):
            context ={
                'form_blueprints':FormBlueprint.objects.all()
            }
            return render(request, 'forms/fb_all.html', context=context)
        else:
            context={
                        'message': "Your team doesn't have permission to manage blueprints"
                    }
            return render(request, 'forms/redirect_to_dashboard.html', context = context)
    except:
        context={
                        'message': "Your team doesn't have permission to manage blueprints"
                    }
        return render(request, 'forms/redirect_to_dashboard.html', context = context)
@login_required
def fb_edit(request, fb_id):#fb is for form blueprint
    fb_object = FormBlueprint.objects.get(pk=fb_id)
    workflow = Workflow.objects.get(formblueprint = fb_object)
    #check if the creator is the one currently logged in
    if request.user.profile!=fb_object.workflow.creator:
        context={
            'title': 'Unauthorised Access',
            'message': 'Unauthorised Access: Only the creator of the form is allowed to access this page'
        }
        return render(request, 'message.html', context=context)
    if fb_object.saved==True:
        context={
            'title': 'Unauthorised Access',
            'message': 'Unauthorised Access: A form blueprint once saved cannot be edited'
        }
        return render(request, 'message.html', context=context)
    context = {
        'fb_object': fb_object,
        'workflow_nodes': workflow.get_flow(),
    }
    return render(request, 'forms/fb_edit.html', context=context)

@login_required
def fb_toggle_activation(request, fb_id):#fb is for form blueprint
    fb_object = FormBlueprint.objects.get(pk=fb_id)
    #check if the creator is the one currently logged in
    if request.user.profile!=fb_object.workflow.creator:
        context={
            'title': 'Unauthorised Access',
            'message': 'Unauthorised Access: Only the creator of the form is allowed to toggle the activation'
        }
        return render(request, 'message.html', context=context)
    #toggle the active attribute and save
    if fb_object.active==True:fb_object.active=False
    else: fb_object.active=True
    fb_object.save()

    return redirect('fb_all')


def fb_create(request):
    if request.method=='POST':
        fb = dict(json.loads(request.POST['fb']))#fb is the form_blueprint
        fb_object = FormBlueprint.objects.get(id=fb["id"])

        if fb_object.saved==True:
            context={
                'title': 'Unauthorised Access',
                'message': 'Unauthorised Access: A form blueprint once saved cannot be edited'
            }
            return render(request, 'message.html', context=context)
        fb_object.update_document(fb)

        #mark form as saved
        fb_object.saved = True
        fb_object.save()

    context={
                    'message': "Response Failed"
                }
    return render(request, 'forms/redirect_to_dashboard.html', context = context)

@login_required
def fb_preview(request, fb_id):
    fb_object = FormBlueprint.objects.get(pk=fb_id)
    if fb_object.saved==False:
        context={
            'title': 'Unauthorised Access',
            'message': 'Unauthorised Access: A form blueprint has to be saved to be previewed'
        }
        return render(request, 'message.html', context=context)
    #get the form blueprint from mongo and parse it to html then pass return the view
    preview_html = fb_object.fetch_preview_html()

    context = {
        'preview_html':preview_html
    }
    return render(request, 'forms/fb_preview.html', context = context)

@login_required
def fb_available_to_instantiate(request):
    available_form_blueprints={}
    #fetch role of the user
    try:
        user_role=TeamHasEmployees.objects.get(employee= request.user.profile).role
    except Exception as e:
        print("in fb_available_to_instantiate: "+str(e))
        return render(request, 'message.html', {'message': "You haven't been assigned a team yet"})
        #fetch form blueprints whose starting node has the role of the user. Only those form blueprints can be used to instantiate a form.

    try:
        head_nodes= Node.objects.filter(associated_role=user_role, prev_node = None)
        forms = [node.get_blueprint() for node in head_nodes if node.get_blueprint().active==True]
        context ={
            'form_blueprints':forms
        }
        return render(request, 'forms/fb_permitted.html', context=context)
    except Exception as e:
        print("in fb_available_to_instantiate: "+str(e))
        return render(request, 'message.html', {'message': "No forms available."})



@login_required
def fi_create(request, fb_id):
    #get the section of the form relevant to this person and render that section
    fb_object = FormBlueprint.objects.get(id=fb_id)
    #for now assuming that it is the first section which is relevant for creation of the form
    section_id = 1
    section_html, node_id = fb_object.fetch_section_html(section_id)

    node_object = Node.objects.get(id=node_id)


    if request.method=="POST":
        #save the  instance in MONGO in the relevant collection
        try:
            sender = request.user.profile
            with transaction.atomic():
                fi_object = FormInstance.objects.create(blueprint=fb_object, current_node=node_object, sender=request.user.profile)

                data = request.POST.dict()
                del data['csrfmiddlewaretoken']
                # data['section_id'] = section_id
                # data['node_id'] = node_id
                fi_object.create_document(data)
                fi_object.send_forward(sender)
                fi_object.save()
                context={
                    'message': "Form Instance Created"
                }
            return render(request, 'forms/redirect_to_dashboard.html', context = context)
        except Exception as e:
            print(e)
            context={
                    'message': "Creation Failed"
                }
            return render(request, 'forms/redirect_to_dashboard.html', context = context)
    else:
        #add the form html tag and the submit button to the section html
        context = {
            'section_html':section_html
        }
        return render(request, 'forms/fi_create.html', context = context)


@login_required
def fi_respond(request, fi_id):
    # get the form instance object
    fi_object = FormInstance.objects.get(id=fi_id)
    sender = request.user.profile
    fb_object = fi_object.blueprint

    if not fi_object.is_user_current_node(sender): return HttpResponse("403: Forbidden")
    #get the section corressponding to the current node of the workflow from the section_id attribute of the node model
    curr_section_id = fi_object.current_node.section_id#curr_section_id is 1-indexed
    is_user_last_node=False
    if not fi_object.current_node.next_node:
        is_user_last_node=True
    section_html, node_id = fb_object.fetch_section_html(curr_section_id)
    if request.method=='POST':
        data = request.POST.copy()#make a copy of the query dict returned which is immutable
        try:
            data['user']=str(request.user)
            print(data)
            del data['csrfmiddlewaretoken']

            with transaction.atomic():
                fi_object.add_response(data)
                if is_user_last_node:
                    fi_object.active=False
                    if data.get('action')=='Submit and Accept':
                        fi_object.accepted=True
                    else:
                        fi_object.accepted=False
                    fi_object.save()
                else:
                    fi_object.send_forward(sender)
                    fi_object.save()
            context={
                    'message': "Response Succesful"
                }
            return render(request, 'forms/redirect_to_dashboard.html', context = context)
        except Exception as e:
            print(e)
            context={
                    'message': "Response Failed"
                }
            return render(request, 'forms/redirect_to_dashboard.html', context = context)
    else:
        context = {
            'section_html': section_html,
            'is_user_last_node': is_user_last_node,
            'fi_id': fi_object.id,
        }
        return render(request, 'forms/fi_respond.html', context=context)

@login_required
def fi_detail(request, fi_id):
    fi_object = FormInstance.objects.get(id=fi_id)
    sender = request.user.profile
    fb_object = fi_object.blueprint

    if not fi_object.is_user_in_workflow(sender): return HttpResponse("403: Forbidden")

    fi_responses = fi_object.fetch_responses()
    fi_comments = FormInstanceHasComment.objects.filter(form_instance=fi_object)
    fi_comments_responses=[]
    # making a combined list of comments and responses
    # a list of tuples (timestmap, identifier, object) , identifier tells whether the object is comment or response, used while rendering
    
    for each in fi_responses:
        aware_date_time=pytz.utc.localize(each['date_time'])
        fi_comments_responses.append((aware_date_time,1,each))

    for each in fi_comments:
        fi_comments_responses.append((each.timestamp,0,each))
    # sort on basis of timestamp
    fi_comments_responses.sort(key=lambda x:x[0])
    for i in fi_comments_responses:
        print(i)
    context = {
        'fi_object': fi_object,
        'fi_responses': fi_comments_responses,
        # 'fi_responses': fi_responses,
        # 'fi_comments': fi_comments
    }
    return render(request, 'forms/fi_detail.html', context = context)

@login_required
def fi_nudge(request, fi_id):
    #TODO: do the nudge procedure here
    #TODO: show some kind of message popup that the nudge has been sent
    return redirect('dashboard')
