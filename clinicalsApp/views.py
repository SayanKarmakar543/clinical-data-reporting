from django.shortcuts import render, redirect, get_object_or_404
from clinicalsApp.models import Patient, ClinicalData
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from clinicalsApp.forms import ClinicalDataForm
from django.db.models import Avg

# Create your views here.
class PatientListView(ListView):
    model = Patient
    # template_name = 'patient_list.html'  # Your template file
    # context_object_name = 'patients'  # Context variable name to use in the template
    paginate_by = 10  # Number of patients per page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Double-check pagination context variables
        context['page_obj'] = context['paginator'].get_page(self.request.GET.get('page', 1))
        return context


class PatientCreateView(CreateView):
    model = Patient
    success_url = reverse_lazy('index')
    fields = ('firstName', 'lastName', 'age')

class PatientUpdateView(UpdateView):
    model = Patient
    tempates = 'clinicalsApp/patient_update.html'
    success_url = reverse_lazy('index')
    fields = ('firstName', 'lastName', 'age')

class PatientDeleteView(DeleteView):
    model = Patient
    template_name = 'clinicalsApp/patient_delete.html'
    success_url = reverse_lazy('index')

# def addData(request, **kwargs):
#     form = ClinicalDataForm()
#     patient = Patient.objects.get(id=kwargs['pk'])
#     if request.method == 'POST':
#         form = ClinicalDataForm(request.POST)
#         if form.is_valid():
#             form.save()
#         return redirect('/')
#     return render(request, 'clinicalsApp/clinicaldata_form.html', {'form':form, 'patient':patient})

# def analyze(request, **kwargs):
    # data = ClinicalData.objects.filter(patient_id=kwargs['pk'])
    # responseData = []
    # for eachEntry in data:
    #     if eachEntry.componentName == 'hw':
    #         heightAndWeight = eachEntry.componentValue.split('/')
    #         if len(heightAndWeight)>1:
    #             feetToMeters = float(heightAndWeight[0])*0.4536
    #             BMI = (float(heightAndWeight[1]))/(feetToMeters*feetToMeters)
    #             bmiEntry = ClinicalData()
    #             bmiEntry.componentName = 'BMI'
    #             bmiEntry.componentValue = BMI
    #             responseData.append(bmiEntry)
    #     responseData.append(eachEntry)
    # return render(request, 'clinicalsApp/generateReport.html',{'data':data})
    

def addData(request, **kwargs):
    patient = get_object_or_404(Patient, id=kwargs['pk'])
    
    if request.method == 'POST':
        blood_pressure = request.POST.get('bloodPressure')
        height = request.POST.get('height')
        weight = request.POST.get('weight')
        heartrate = request.POST.get('heartrate')

        # Create a ClinicalData instance
        clinical_data = ClinicalData(
            bloodPressure=blood_pressure,
            height=height,
            weight=weight,
            heartrate=heartrate,
            patient=patient  # Associate with the patient
        )
        clinical_data.save()

        return redirect('/')  # Redirect after saving the data

    # Fetch all patients for the dropdown
    patients = Patient.objects.all()

    context = {
        'patient': patient,
        'patients': patients,
    }
    return render(request, 'clinicalsApp/clinicaldata_form.html', context)

def analyze_data(request, pk):
    # Fetch all clinical data for the patient using pk (which is patient_id)
    clinical_data = ClinicalData.objects.filter(patient__id=pk).order_by('-measureDateTime')

    if not clinical_data.exists():
        return render(request, 'clinicalsApp/analyze.html', {
            'error': 'No clinical data available for this patient.'
        })
    
    # Analyze the data
    latest_data = clinical_data.first()
    average_blood_pressure = clinical_data.aggregate(Avg('bloodPressure'))
    average_height = clinical_data.aggregate(Avg('height'))
    average_weight = clinical_data.aggregate(Avg('weight'))
    average_heartrate = clinical_data.aggregate(Avg('heartrate'))

    # Calculate BMI using the latest height and weight (BMI = weight / height^2)
    if latest_data.height > 0:
        bmi = latest_data.weight / (latest_data.height ** 2)
    else:
        bmi = None

    # Extract systolic and diastolic values from blood pressure string
    if latest_data.bloodPressure:
        try:
            systolic, diastolic = map(int, latest_data.bloodPressure.split('/'))
        except ValueError:
            systolic, diastolic = None, None
    else:
        systolic, diastolic = None, None

    # Detect if blood pressure or heart rate is abnormal
    abnormal_blood_pressure = (systolic is not None and (systolic > 140 or systolic < 90)) or \
                               (diastolic is not None and (diastolic > 90 or diastolic < 60))
    abnormal_heartrate = latest_data.heartrate > 100 or latest_data.heartrate < 60

    return render(request, 'clinicalsApp/analyze.html', {
        'clinical_data': clinical_data,
        'latest_data': latest_data,
        'average_blood_pressure': average_blood_pressure['bloodPressure__avg'],
        'average_height': average_height['height__avg'],
        'average_weight': average_weight['weight__avg'],
        'average_heartrate': average_heartrate['heartrate__avg'],
        'bmi': bmi,
        'abnormal_blood_pressure': abnormal_blood_pressure,
        'abnormal_heartrate': abnormal_heartrate
    })
