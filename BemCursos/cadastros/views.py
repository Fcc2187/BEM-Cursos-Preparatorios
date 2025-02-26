from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Aluno
from django.contrib import messages
from .mediators import TurmaMediator, AlunoMediator, SimuladoMediator, NotaMediator, RankingMediator, RankingResponsavelMediator
from datetime import datetime
from django.urls import reverse
from django.views.decorators.csrf import requires_csrf_token


def home(request):
    return redirect('login')

class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        logout(request)
        return render(request, self.template_name)

    def post(self, request):
        user_type = request.POST.get('user_type')  
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  
            if request.user.is_superuser:
                return redirect('turmas') 
            
            elif user_type == 'responsavel':
                try:
                    aluno = Aluno.objects.get(user=user)
                    return redirect(reverse('responsavel'))
                except Aluno.DoesNotExist:
                    messages.error(request, 'Nenhum aluno encontrado para este responsável.')
                    return render(request, self.template_name)
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
            return render(request, self.template_name)
        
        messages.error(request, 'Usuário, senha ou aluno inválidos.')
        return render(request, self.template_name)

        
class TurmaView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name_list = 'turmas.html'
    template_name_add = 'adicionar_turma.html'

    def get(self, request, turma_id=None):
        if request.path.endswith('adicionar/'):
            unidades = TurmaMediator.listar_unidades()  
            return render(request, self.template_name_add, {'unidades': unidades})
        else:
            unidade_id = request.GET.get('unidade')
            unidades = TurmaMediator.listar_unidades()  
            turmas = TurmaMediator.listar_turmas_por_unidade(unidade_id) if unidade_id else TurmaMediator.listar_turmas()
            return render(request, self.template_name_list, {'turmas': turmas, 'unidades': unidades, 'unidade_selecionada': unidade_id})

    def post(self, request, turma_id=None):
        if 'method' in request.POST and request.POST['method'] == 'DELETE':
            if turma_id is not None:
                resultado = TurmaMediator.excluir_turma(turma_id)  
                return JsonResponse(resultado)
            return JsonResponse({'error': 'ID da turma não fornecido'}, status=400)

        nome = request.POST.get('nome')
        unidade_id = request.POST.get('unidade')
        TurmaMediator.adicionar_turma(nome, unidade_id)  
        return redirect('turmas')

    def excluir_turma(self, turma_id):
        try:
            response = TurmaMediator.excluir_turma(turma_id)
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class AlunoView(LoginRequiredMixin, View):
    login_url = '/login/'
    template_name_list = 'alunos.html'
    template_name_add = 'adicionar_aluno.html'

    def get(self, request, turma_id=None):
        if request.path.endswith('adicionar/'):
            return render(request, self.template_name_add, {'turma_id': turma_id})
        elif turma_id:
            # Buscar a turma pelo ID para pegar o nome
            turma = TurmaMediator.obter_turma_especifica(turma_id)
            alunos = AlunoMediator.listar_alunos(turma_id)
            return render(request, self.template_name_list, {'alunos': alunos, 'turma_id': turma_id, 'turma_nome': turma.nome})
        else:
            return redirect('turmas')

    def post(self, request, turma_id=None):
        if 'remover_aluno_id' in request.POST:
            aluno_id = request.POST.get('remover_aluno_id')
            resultado = AlunoMediator.remover_aluno(aluno_id)
            messages.success(request, resultado['status'])
            return redirect('alunos', turma_id=turma_id)

        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        cpf = request.POST.get('cpf')
        data_nascimento_str = request.POST.get('data_nascimento')

        try:
            # Converter a data de nascimento
            data_nascimento = datetime.strptime(data_nascimento_str, "%Y-%m-%d").date()

            # Verificar se o CPF é válido
            aluno_temp = Aluno(
                nome=nome,
                sobrenome=sobrenome,
                cpf=cpf,
                data_nascimento=data_nascimento,
                turma_id=turma_id
            )
            if not aluno_temp.validar_cpf():
                raise ValueError("CPF inválido. Verifique o número e tente novamente.")

            # Adicionar aluno
            is_ver_geral = bool(request.POST.get('is_ver_geral'))
            AlunoMediator.adicionar_aluno(nome, sobrenome, cpf, data_nascimento, turma_id, is_ver_geral)
            messages.success(request, "Aluno e usuário criados com sucesso!")
            return redirect('alunos', turma_id=turma_id)

        except ValueError as e:
            # Captura erros específicos e exibe mensagens amigáveis
            messages.error(request, str(e))
            return render(request, self.template_name_add, {'turma_id': turma_id})

        except Exception as e:
            # Tratamento genérico para qualquer outro erro
            messages.error(request, "Ocorreu um erro inesperado")
            return render(request, self.template_name_add, {'turma_id': turma_id})

    
    
class SimuladoView(View):
    template_name_list = 'simulados.html'
    template_name_add = 'adicionar_simulado.html'

    def get(self, request, simulado_id=None):
        if request.path.endswith('adicionar/'):
            return render(request, self.template_name_add)
        else:
            simulados = SimuladoMediator.listar_simulados()
            return render(request, self.template_name_list, {'simulados': simulados})

    def post(self, request, simulado_id=None):
        if simulado_id:
            SimuladoMediator.excluir_simulado(simulado_id)
            return redirect('simulados')
        
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo')
        data = request.POST.get('data')

        if not nome or not tipo or not data:
            return JsonResponse({'error': 'Todos os campos são obrigatórios!'}, status=400)

        SimuladoMediator.adicionar_simulado(nome, tipo, data)
        return redirect('simulados')


class NotaView(View):
    template_name = 'notas_simulado.html'

    def get(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        alunos = NotaMediator.obter_alunos()
        turmas = TurmaMediator.obter_turmas()
        return render(request, self.template_name, {
            'simulado': simulado,
            'alunos': alunos,
            'turmas': turmas
        })

    def post(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        NotaMediator.salvar_notas(simulado_id, request)

        messages.success(request, "Notas salvas com sucesso!")
        return redirect('notas_simulado', simulado_id=simulado.id)


class RankingView(View):
    template_name = 'ranking.html'

    def get(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        rankings = RankingMediator.calcular_rankings(simulado)

        return render(request, self.template_name, {
            'simulado': simulado,
            'rankings': rankings
        })

class RankingMatematicaView(View):
    template_name = 'ranking_matematica.html'

    def get(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        rankings = RankingMediator.calcular_ranking_matematica(simulado)

        return render(request, self.template_name, {
            'simulado': simulado,
            'rankings': rankings
        })

class RankingPortuguesView(View):
    template_name = 'ranking_portugues.html'

    def get(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        rankings = RankingMediator.calcular_ranking_portugues(simulado)

        return render(request, self.template_name, {
            'simulado': simulado,
            'rankings': rankings
        })
    

class RankingTurmaView(View):
    template_name = 'rankingTurma.html'

    def get(self, request, simulado_id, turma_id=None):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        turmas = TurmaMediator.listar_turmas()
        turma_id = turma_id or request.GET.get('turma_id')
        if turma_id:
            rankings = RankingMediator.calcular_rankingTurma(simulado, turma_id)
            turma = TurmaMediator.obter_turma(turma_id)
        else:
            rankings = []
            turma = None
        return render(request, self.template_name, {
            'simulado': simulado,
            'rankings': rankings,
            'turmas': turmas,
            'turma': turma,
        })

    def post(self, request, simulado_id, turma_id=None):
        turma_id = request.POST.get('turma_id')
        return redirect('ranking_por_turma', simulado_id=simulado_id, turma_id=turma_id)
    

class ResponsavelView(LoginRequiredMixin, View):
    template_name = 'responsavel.html'
    def get(self, request):
        aluno = AlunoMediator.obter_aluno(request.user)
        simulados = SimuladoMediator.listar_simulados()
        turmas = TurmaMediator.obter_turmas()
        return render(request, self.template_name, {'aluno': aluno, 'simulados': simulados, 'turmas': turmas})

    def post(self, request):
        aluno = AlunoMediator.obter_aluno(request.user)
        simulados = SimuladoMediator.listar_simulados()
        turmas = TurmaMediator.obter_turmas()
        return render(request, self.template_name, {'aluno': aluno, 'simulados': simulados, 'turmas': turmas})
    


class RankingPorTurmaResponsavelView(LoginRequiredMixin, View):
    template_name = 'ranking_turma_responsavel.html'
    def get(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        aluno = AlunoMediator.obter_aluno(request.user)
        turma = aluno.turma
        rankings_turma = RankingResponsavelMediator.calcular_rankings_turma(simulado, turma.id)
        ranking_aluno = RankingResponsavelMediator.calcular_ranking_aluno_turma(simulado, aluno.id, turma.id)

        return render(request, self.template_name, {
            'aluno': aluno,
            'simulado': simulado,
            'rankings': rankings_turma,
            'ranking_aluno': ranking_aluno,
            'turma': turma,
        })

class RankingGeralResponsavelView(LoginRequiredMixin, View):
    template_name = 'ranking_geral_responsavel.html'

    def get(self, request, simulado_id):
        simulado = SimuladoMediator.obter_simulado(simulado_id)
        aluno = AlunoMediator.obter_aluno(request.user)
        aluno_ranking = RankingResponsavelMediator.calcular_ranking_aluno(simulado, aluno.id)

        return render(request, self.template_name, {
            'aluno': aluno,
            'simulado': simulado,
            'aluno_ranking': aluno_ranking,
        })
    
class SimuladosResponsavelView(LoginRequiredMixin, View):
    template_name = 'simulados_responsavel.html'

    def get(self, request):
        simulados = SimuladoMediator.listar_simulados()
        aluno = AlunoMediator.obter_aluno(request.user)
        turma = aluno.turma

        return render(request, self.template_name, {
            'simulados': simulados,
            'aluno': aluno,
            'turma': turma,
        })
    
@requires_csrf_token
def csrf_failure(request, reason=""):
    messages.error(request, "Sessão expirada. Faça login novamente.")
    return redirect('login')
