from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.util.files import upload
from gargantext.models import *
from gargantext.constants import *

from gargantext.util.scheduling import scheduled
from gargantext.util.toolchain import parse_extract

from datetime import datetime
from collections import defaultdict
import re


@requires_auth
def overview(request):
    '''This view show all projects for a given user.
    Each project is described with hyperdata that are updateded on each following view.
    To each project, we can link a resource that can be an image.
    '''

    user = cache.User[request.user.username]

    # If POST method, creates a new project...
    if request.method == 'POST':
        name = str(request.POST['name'])
        if name != '':
            new_project = Node(
                user_id = user.id,
                typename = 'PROJECT',
                name = name,
            )
            session.add(new_project)
            session.commit()

    # list of projects created by the logged user
    user_projects = user.nodes(typename='PROJECT')

    # list of contacts of the logged user
    contacts_projects = list(user.contacts_nodes(typename='PROJECT'))

    # render page
    return render(
        template_name = 'pages/projects/overview.html',
        request = request,
        context = {
            'debug': settings.DEBUG,
            'date': datetime.now(),
            # projects owned by the user
            'number': len(user_projects),
            'projects': user_projects,
            # projects owned by the user's contacts
            'common_users': (contact for contact, projects in contacts_projects),
            'common_projects': sum((projects for contact, projects in contacts_projects), []),
        },
    )


from django.utils.translation import ugettext_lazy
class NewCorpusForm(forms.Form):
    type = forms.ChoiceField(
        choices = enumerate(resource_type['name'] for resource_type in RESOURCETYPES),
        widget = forms.Select(attrs={'onchange':'CustomForSelect( $("option:selected", this).text() );'})
    )
    name = forms.CharField( label='Name', max_length=199 , widget=forms.TextInput(attrs={ 'required': 'true' }))
    file = forms.FileField()
    def clean_file(self):
        file_ = self.cleaned_data.get('file')
        if len(file_) > 1024 ** 3: # we don't accept more than 1GB
            raise forms.ValidationError(ugettext_lazy('File too heavy! (>1GB).'))
        return file_

@requires_auth
def project(request, project_id):
    # current user
    user = cache.User[request.user.username]
    # viewed project
    project = session.query(Node).filter(Node.id == project_id).first()
    if project is None:
        raise Http404()
    if not user.owns(project):
        raise HttpResponseForbidden()

    # new corpus
    if request.method == 'POST':
        corpus = project.add_child(
            name = request.POST['name'],
            typename = 'CORPUS',
        )
        corpus.add_resource(
            type = int(request.POST['type']),
            path = upload(request.FILES['file']),
        )
        session.add(corpus)
        session.commit()
        scheduled(parse_extract)(corpus.id)

    # corpora within this project
    corpora = project.children('CORPUS').all()
    sourcename2corpora = defaultdict(list)
    for corpus in corpora:
        # we only consider the first resource of the corpus to determine its type
        resource = corpus.resources()[0]
        resource_type_name = RESOURCETYPES[resource['type']]['name']
        # add some data for the viewer
        corpus.count = corpus.children('DOCUMENT').count()
        status = corpus.status()
        if status is not None and not status['complete']:
            corpus.status_message = '(in progress: %s, %d complete)' % (
                status['action'].replace('_', ' '),
                status['progress'],
            )
        else:
            corpus.status_message = ''
        # add
        sourcename2corpora[resource_type_name].append(corpus)
    # source & their respective counts
    total_documentscount = 0
    sourcename2documentscount = defaultdict(int)
    for sourcename, corpora in sourcename2corpora.items():
        sourcename = re.sub(' \(.*$', '', sourcename)
        count = corpus.children('DOCUMENT').count()
        sourcename2documentscount[sourcename] += count
        total_documentscount += count
    donut = [
        {   'source': sourcename,
            'count': count,
            'part' : round(count * 100.0 / total_documentscount, 1) if total_documentscount else 0,
        }
        for sourcename, count in sourcename2documentscount.items()
    ]
    # response!
    return render(
        template_name = 'pages/projects/project.html',
        request = request,
        context = {
            'form': NewCorpusForm,
            'user': request.user,
            'date': datetime.now(),
            'project': project,
            'donut': donut,
            'list_corpora': dict(sourcename2corpora),
            'whitelists': [],
            'blacklists': [],
            'cooclists': [],
            'number': len(corpora),
            'query_size': QUERY_SIZE_N_DEFAULT,
        },
    )