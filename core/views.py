from django.shortcuts import render,redirect
from django.template import loader
from django.contrib.auth import login, authenticate, logout
from django.http import HttpResponse
from django.core.files.storage import default_storage

import uuid
import os

from .forms import SignupForm
import json

from core.docxGeneration import generate_docx

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
    error = []

    if request.method == 'POST':

        # Header Data Validation
        receivedFile = request.FILES.get('file')
        headerData = {
            'Course_Unit': request.POST.get('Course_Unit',''),
            'Instructor': request.POST.get('Instructor',''),
            'Course': request.POST.get('Course',''),
        }
        
        if not receivedFile:
            error.append('Nenhum arquivo selecionado.')

        if headerData['Course_Unit'].strip() == '':
            error.append('O campo "Unidade Curricular" é obrigatório.')

        if headerData['Instructor'].strip() == '':
            error.append('O campo "Docente" é obrigatório.')

        if headerData['Course'].strip() == '':
            error.append('O campo "Curso" é obrigatório.')

        if error:
            return render(request, 'home.html', {'error': error})

        #print("receivedFile>>>>",receivedFile[0])
        # File Data Validation (JSON LISTA)
        try:
            jsonData = json.load(receivedFile)   # Arquivo inteiro carregado
            print("jsonData >>>>", jsonData)
            print("jsonData[0] >>>>", jsonData[0])
            if not isinstance(jsonData, list):
                error.append('O arquivo deve ser uma lista de questões em formato JSON.')

            elif len(jsonData) == 0:
                error.append('Arquivo JSON está vazio.')

            else:
                for idx, question in enumerate(jsonData, start=1):

                    # Verifica campos obrigatórios
                    missing = fields - question.keys()
                    for field in missing:
                        error.append(f'Campo obrigatório "{field}" ausente na questão {idx}.')

                    # Validação de alternativas
                    alts = question.get('Alternativas', [])

                    if len(alts) < 3:
                        error.append(f'A questão {idx} deve conter pelo menos 3 alternativas.')

                    if len(alts) > 4:
                        error.append(f'A questão {idx} deve conter no máximo 4 alternativas.')

                    for alt in alts:
                        if alt.get('texto', '').strip() == '':
                            error.append(f'A questão {idx} contém alternativa vazia.')
                        if alt.get('gabarito') not in [True, False]:
                            error.append(f'O gabarito da questão {idx} deve ser True ou False.')

                    if sum(1 for alt in alts if alt.get('gabarito') is True) != 1:
                        error.append(f'A questão {idx} deve ter exatamente 1 gabarito.')

        except Exception:
            error.append('Arquivo JSON inválido.')

        if error:
            return render(request, 'home.html', {'error': error})

        main_buffer,answer_Buffer = generate_docx(headerData, jsonData)
        request.session['test_name'] = headerData['Course_Unit']
        request.session['main_doc'] = main_buffer.getvalue().hex()
        request.session['answers_doc'] = answer_Buffer.getvalue().hex()
        
        
        return render(request, 'home.html', {'download_ready': True})


    return render(request, 'home.html')

@login_required
def download_main_test(request):
    hex_data = request.session.get('main_doc', None)
    test_name = request.session.get('test_name','prova')
    if not hex_data:
        return redirect('home')
    
    data = bytes.fromhex(hex_data)
    
    
    return HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{test_name}_prova.docx"'}
    )
    
@login_required
def download_answer_test(request):
    hex_data = request.session.get('answers_doc',None)
    test_name = request.session.get('test_name','prova')
    if not hex_data:
        return redirect('home')
    
    data = bytes.fromhex(hex_data)
    
    
    return HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{test_name}_gabarito.docx"'}
    )

@login_required
def profile_view(request):
    template = loader.get_template('profile.html')
    return render(request, 'profile.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('home')




