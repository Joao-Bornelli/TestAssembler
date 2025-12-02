from django.shortcuts import render,redirect
from django.template import loader
from django.contrib.auth import login, authenticate, logout
from .forms import SignupForm
import json

from django.contrib.auth.decorators import login_required
# Create your views here.

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request=request, username=username, password=password)
        print('>>usuario',user)
        print('>>username',username)
        print('>>password',password)
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            error = "Usuario ou senha incorretos!"
    
    return render(request, 'login.html', {'error': error})

def signup_view(request):
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect('home')
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {'form': form})


@login_required
def home_view(request):
    fields = {'Contexto','Comando','Alternativas','Justificativa do Gabarito','Justificativa dos Distratores','Informações Essenciais'}
    
    if request.method == 'POST':
        receivedFile = request.FILES.get('file')
        if not receivedFile:
            return render(request, 'home.html', {'error': 'Nenhum arquivo selecionado.'})
        
        try:
            jsonData = json.load(receivedFile)
        except Exception:
            return render(request, 'home.html', {'error': 'Arquivo inválido.'})
        
        if isinstance(jsonData, list):
            if len(jsonData) == 0:
                return render(request, 'home.html', {'error': 'Arquivo JSON está vazio.'})
            else:
                jsonData = jsonData[0]
            
        missing = fields - jsonData.keys() 
        for field in missing:
            return render(request, 'home.html', {'error': f'Campo obrigatório "{field}" ausente no arquivo.'})
        
        if len(jsonData['Alternativas'])<3:
            return render(request, 'home.html', {'error': 'O campo "Alternativas" deve conter pelo menos 3 itens.'})
        
        if len(jsonData['Alternativas'])>4:
            return render(request, 'home.html', {'error': 'O campo "Alternativas" deve conter no máximo 4 itens.'})
        
        for alt in jsonData['Alternativas']:
            if alt['texto'].strip() == '':
                return render(request, 'home.html', {'error': 'As alternativas não podem estar vazias.'})
            if alt['gabarito'] not in [True,False]:
                return render(request, 'home.html', {'error': 'O campo "gabarito" das alternativas deve ser True ou False.'})
        
        if sum(1 for alt in jsonData['Alternativas'] if alt.get('gabarito')==True) != 1:
            return render(request, 'home.html', {'error': 'Deve haver ao menos uma alternativa marcada como gabarito (True).'})
        #teste     
        return render(request, 'home.html', {'success': 'Arquivo processado com sucesso!', 'data': jsonData})
        
    
    return render(request, 'home.html')

@login_required
def profile_view(request):
    template = loader.get_template('profile.html')
    return render(request, 'profile.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('home')


