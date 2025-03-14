from django.urls import reverse
from django.views.generic import ListView, TemplateView
from crisp_modals.views import ModalUpdateView, ModalCreateView, ModalDeleteView
from demo.example.forms import PersonForm, InstitutionForm, SubjectForm
from demo.example.models import Person, Institution, Subject
from itemlist.views import ItemListView


# Create your views here.
class PersonList(ListView):
    model = Person
    template_name = 'example/person_list.html'
    paginate_by = 15


class FancyPersonList(ItemListView):
    model = Person
    template_name = 'list.html'
    list_columns = ['first_name', 'last_name', 'age', 'type', 'institution']
    list_search = ['first_name', 'last_name', 'age', 'type', 'bio', 'institution__name']
    list_filters = ['type', 'created']
    list_title = 'Fancy Person List'
    link_url = 'person-edit'
    link_attr = 'data-modal-url'
    paginate_by = 15


class InstitutionList(ListView):
    model = Institution
    template_name = 'example/institution_list.html'
    paginate_by = 15


class SubjectList(ListView):
    model = Subject
    template_name = 'example/subject_list.html'
    paginate_by = 15


class EditPerson(ModalUpdateView):
    model = Person
    form_class = PersonForm


class AddPerson(ModalCreateView):
    model = Person
    form_class = PersonForm


class EditInstitution(ModalUpdateView):
    model = Institution
    form_class = InstitutionForm


class AddInstitution(ModalCreateView):
    model = Institution
    form_class = InstitutionForm


class EditSubject(ModalUpdateView):
    model = Subject
    form_class = SubjectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['delete_url'] = reverse('subject-delete', kwargs={'pk': self.object.pk})
        return kwargs


class AddSubject(ModalCreateView):
    model = Subject
    form_class = SubjectForm


class DeletePerson(ModalDeleteView):
    model = Person


class DeleteInstitution(ModalDeleteView):
    model = Institution


class DeleteSubject(ModalDeleteView):
    model = Subject


class HomeView(TemplateView):
    template_name = "example/home.html"

