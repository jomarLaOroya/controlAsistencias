from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import HttpResponse
from sitioWeb import utils
from babel.dates import format_date

from datetime import datetime
import locale
from sitioWeb.models import *

# Create your views here.

def login_docente(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Credenciales Incorrectas. Intentelo Nuevamente.")
    return render(request, "login_docentes.html")

def salir(request):
    logout(request)
    return redirect('/')

def buscar_asistencia(request):
    
    mensajes = []
    if request.method == 'POST':
        dni = request.POST.get('dni_alumno')
        alumno = Alumno.objects.filter(dni=dni)
        if alumno:
            asist = Asistencia.objects.filter(dni_almn=dni).order_by('-id')[:5]
            hora_limite = datetime.strptime("07:50:00", "%H:%M:%S").time()
            hora_inicio = datetime.strptime("07:00:00", "%H:%M:%S").time()
            context = {"alumno":alumno, "asistencias":asist, "hora_limite":hora_limite, "hora_inicio":hora_inicio}
            return render(request, "mostrar_asistencia.html", context)
        else:
            mensajes.append("DNI INCORRECTO")
            context = {"mensajes":mensajes}
            return render(request, "buscar_asistencia.html", context)
            
    return render(request, "buscar_asistencia.html")

def inicio(request):
    
    return render(request, "inicio.html")

def lista_alumnos(request):
    
    if request.method == "POST":
        grado = request.POST.get('grado')
        seccion = request.POST.get('seccion')
        
        alumnos = Alumno.objects.filter(grado__icontains=grado, seccion__icontains=seccion).order_by('apellido_nombre')
        if alumnos:
            context = {"alumnos":alumnos, "grado":grado, "seccion":seccion}
            return render(request, "lista_alumnos.html", context)
        else:
            mensaje = "SIN ALUMNOS REGISTRADOS"
            context = {"mensaje":mensaje, "grado":grado, "seccion":seccion}
            return render(request, "lista_alumnos.html", context)
    
    return render(request, "lista_alumnos.html")

def asistencias(request):
    
    return render(request, "asistencias.html")

def lista_asistencias(request):
    
    if request.method == "POST":
        fecha = datetime.now().strftime('%Y-%m-%d')
        grado = request.POST.get('grado')
        seccion = request.POST.get('seccion')
        asistencias = Asistencia.objects.filter(fecha_registro__icontains=fecha, grado__icontains=grado, seccion__icontains=seccion).order_by('alumno')
        context = {"asistencias":asistencias, "fecha":fecha}
        
    return render(request, "asistencias_salon.html", context)

def editar_asistencia(request, id):
    
    asistencia = Asistencia.objects.get(id=id)
    context = {"asistencia":asistencia}
       
    return render(request, "editar_asistencia.html", context)

def asistencia_editada(request):
    
    id = int(request.POST.get('id'))
    nueva_hora = request.POST.get('hora')
    
    asistencia = Asistencia.objects.get(id=id)
    asistencia.hora_registro = nueva_hora
    asistencia.save()
    
    return redirect('/asistencias/')

def reportes(request):
    
    return render(request, "reportes.html")

def generar_reporte(request):
    
    locale.setlocale(locale.LC_TIME, 'es_PE.UTF-8')
    fecha = datetime.now().strftime('%Y-%m-%d')
    ahora = datetime.now()
    fecha_archivo = format_date(ahora, format='full', locale='es')
    grado = request.POST.get('grado')
    seccion = request.POST.get('seccion')
    hora_tarde = request.POST.get('hora_tarde')
    asistencias = Asistencia.objects.filter(fecha_registro__icontains=fecha, grado__icontains=grado, seccion__icontains=seccion)
    context = {"asistencias":asistencias, "grado":grado, "seccion":seccion, "tarde":hora_tarde, "fecha":fecha_archivo}

    pdf = utils.render_pdf("modelo_reporte.html", context)
    nombre_archivo = str(grado) +"_"+ str(seccion) +" "+ str(fecha)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={nombre_archivo}.pdf'
    return response

def resumen_reporte(request):
    
    locale.setlocale(locale.LC_TIME, 'es_PE.UTF-8')
    fecha = datetime.now().strftime('%Y-%m-%d')
    ahora = datetime.now()
    fecha_archivo = format_date(ahora, format='full', locale='es')
    hora_inicio = "07:00:00"
    hora_tarde = request.POST.get('hora_tarde')
    hora_final = "10:00:00"
    grados = ["PRIMERO", "SEGUNDO", "TERCERO", "CUARTO", "QUINTO"]
    secciones = ["A", "B", "C", "D", "E", "F", "G"]
    alumnos = []
    registros = []
    asistencias_puntuales = []
    asistencias_tarde = []
    faltas = []
    sumatoria_alumnos = []
    sumatoria_registros = []
    sumatoria_puntuales = []
    sumatoria_faltas = []
    sumatoria_tardes = []
    for grado in grados:
        suma_alumnos = 0
        suma_registros = 0
        suma_puntuales = 0
        suma_faltas = 0
        suma_tardes = 0
        for seccion in secciones:
            n_alumno = Alumno.objects.filter(grado__icontains=grado, seccion__icontains=seccion)
            n_registros = Asistencia.objects.filter(grado__icontains=grado, seccion__icontains=seccion, fecha_registro__icontains=fecha)
            n_puntuales = Asistencia.objects.filter(grado__icontains=grado, seccion__icontains=seccion,
                                                    fecha_registro__icontains=fecha, hora_registro__range=(hora_inicio, hora_tarde))
            n_tarde = Asistencia.objects.filter(grado__icontains=grado, seccion__icontains=seccion,
                                                fecha_registro__icontains=fecha, hora_registro__range=(hora_tarde, hora_final))
            n_faltas = Asistencia.objects.filter(grado__icontains=grado, seccion__icontains=seccion, fecha_registro__icontains=fecha, hora_registro="00:00:00")
            faltas.append(len(n_faltas))
            asistencias_puntuales.append(len(n_puntuales))
            asistencias_tarde.append(len(n_tarde))
            registros.append(len(n_registros))
            alumnos.append(len(n_alumno))
            suma_alumnos = suma_alumnos + len(n_alumno)
            suma_registros = suma_registros + len(n_registros)
            suma_puntuales = suma_puntuales + len(n_puntuales)
            suma_faltas = suma_faltas + len(n_faltas)
            suma_tardes = suma_tardes + len(n_tarde)
        
        sumatoria_alumnos.append(suma_alumnos)
        sumatoria_registros.append(suma_registros)
        sumatoria_puntuales.append(suma_puntuales)
        sumatoria_tardes.append(suma_tardes)
        sumatoria_faltas.append(suma_faltas)
    
    sumatoria_total = []
    sumatoria_total.append(sum(sumatoria_alumnos))
    sumatoria_total.append(sum(sumatoria_registros))
    sumatoria_total.append(sum(sumatoria_puntuales))
    sumatoria_total.append(sum(sumatoria_faltas))
    sumatoria_total.append(sum(sumatoria_tardes))
    
    context = {"fecha":fecha_archivo, "alumnos":alumnos, "registros":registros, "puntuales":asistencias_puntuales,
               "tarde":asistencias_tarde, "faltas":faltas, "suma_alumnos":sumatoria_alumnos, "suma_registros":sumatoria_registros,
               "suma_puntuales":sumatoria_puntuales, "suma_tardes":sumatoria_tardes, "suma_faltas":sumatoria_faltas,
               "sumatoria_total":sumatoria_total}
    
    pdf = utils.render_pdf("resumen_reporte.html", context)
    nombre_archivo = "Cuadro Resumen " + str(fecha)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={nombre_archivo}.pdf'
    return response
    
def eliminar_alumno(request, id):
    
    alumno = Alumno.objects.get(id=id)
    alumno.delete()
    
    return redirect('/')

def editar_alumno(request, id):
    
    alumno = Alumno.objects.get(id=id)
    context = {'alumno':alumno}
    return render(request, "editar_alumno.html", context)

def alumno_editado(request):
    
    id = int(request.POST.get('id'))
    nuevo_nombre = request.POST.get('apellido_nombre')
    nueva_seccion = request.POST.get('seccion')
    
    alumno = Alumno.objects.get(id=id)
    alumno.apellido_nombre = nuevo_nombre
    alumno.seccion = nueva_seccion
    alumno.save()
    
    return redirect('/')

