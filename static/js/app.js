/**
 * TruthLens — Client Application Controller
 * Handles tab toggling, character counting, sample loading, AJAX analysis submission,
 * progressive status updates, deletion confirmation modals, and JSON export.
 */

// Global sample news stories for easy demonstration and viva presentation
const DEMO_SAMPLES = {
    en: {
        title: "Sensational Claims on Revolutionary Herbal Panacea",
        text: `Urgent medical emergency! A groundbreaking new natural tonic has been completely suppressed by big global pharmaceutical cartels. 

Independent whistleblowers recently revealed that 95% of patients suffering from chronic respiratory distress recovered within 48 hours without any pharmaceutical intervention. Leading doctors are terrified that the public will uncover this miracle cure. 

Government health ministries held a secret emergency summit last Tuesday to regulate traditional wellness practitioners. Everyone knows that conventional hospitals only care about quarterly profits, while ordinary citizens suffer. 

Don't let your family become victims of corporate greed—share this message immediately before it gets taken down by tech algorithms!`
    },
    hi: {
        title: "नई कृषि सब्सिडी नीति पर चिंताजनक दावे",
        text: `अत्यंत चिंताजनक खबर! हाल ही में घोषित नई केंद्रीय वित्तीय नीति के कारण राज्य के 45% से अधिक ग्रामीण उत्पादकों को भारी घाटा होने का दावा किया जा रहा है।

विपक्ष के एक नेता ने आरोप लगाया कि मंत्रालय ने बिना किसी सार्वजनिक परामर्श के 15 मार्च को गुप्त रूप से नई गाइडलाइंस जारी की हैं। उन्होंने कहा कि "सभी जानते हैं कि यह नीति केवल कुछ बड़े कॉरपोरेट्स को लाभ पहुंचाने के लिए बनाई गई है।"

विशेषज्ञों का कहना है कि जमीनी स्तर पर उत्पादन में भारी गिरावट दर्ज की जा रही है और किसान संगठन अब 20 तारीख से राष्ट्रव्यापी आंदोलन शुरू करने की योजना बना रहे हैं। यदि इस पर तुरंत ध्यान नहीं दिया गया तो देश में गंभीर खाद्य संकट पैदा हो जाएगा।`
    },
    te: {
        title: "రాష్ట్ర పారిశ్రామిక విధానంపై తాజా ప్రకటన",
        text: `రాష్ట్రంలో కొత్త పారిశ్రామిక నిబంధనల అమలు వల్ల ఉపాధి రంగంలో తీవ్ర మార్పులు చోటుచేసుకుంటున్నాయని నివేదికలు పేర్కొంటున్నాయి.

సంబంధిత శాఖ గడిచిన త్రైమాసికంలో 30 శాతం పెట్టుబడుల పెరుగుదలను నమోదు చేసినట్లు ప్రకటించింది. అయితే, క్షేత్రస్థాయిలో వేలాది మంది కార్మికులు దీని ప్రభావంతో అనిశ్చితిని ఎదుర్కొంటున్నారు.

ప్రభుత్వ వర్గాలు నిన్న ప్రత్యేక సమావేశాన్ని ఏర్పాటు చేసి నూతన మార్గదర్శకాలను ఆమోదించాయి. ప్రతి ఒక్కరూ ఈ విధానాన్ని పరిశీలించాలని, తక్షణ నివారణ చర్యలు చేపట్టాలని యూనియన్ ప్రతినిధులు డిమాండ్ చేస్తున్నారు.`
    },
    ta: {
        title: "புதிய பொது நலக் கொள்கை குறித்த முக்கிய அறிவிப்பு",
        text: `அவசர மற்றும் முக்கிய செய்தி! மாநிலத்தில் அண்மையில் அமல்படுத்தப்பட்ட புதிய பொதுப் பங்கீட்டுத் திட்டம் குறித்து பொதுமக்கள் மத்தியில் தீவிர விவாதம் எழுந்துள்ளது.

சம்பந்தப்பட்ட துறை கடந்த மாதத்தில் 35% வரை திட்டப் பயன்கள் அதிகரித்துள்ளதாக அறிவித்துள்ளது. இருப்பினும், உண்மை நிலவரத்தை மூடிமறைக்க அதிகாரிகள் முயற்சிப்பதாக எதிர்க்கட்சித் தலைவர்கள் குற்றம் சாட்டுகின்றனர்.

நேற்று நடைபெற்ற உயர்மட்ட ஆலோசனைக் கூட்டத்தில் பல முக்கிய முடிவுகள் எடுக்கப்பட்டன. பொதுமக்கள் அனைவரும் உடனடியாக விழிப்புடன் செயல்பட வேண்டும் என்று சமூக ஆர்வலர்கள் கோரிக்கை விடுத்துள்ளனர்.`
    },
    kn: {
        title: "ರಾಜ್ಯದ ಹೊಸ ಕೃಷಿ ಸಹಾಯಧನ ಯೋಜನೆ ಕುರಿತು ವರದಿ",
        text: `ತುರ್ತು ಸಾರ್ವಜನಿಕ ಮಾಹಿತಿ! ರಾಜ್ಯ ಸರ್ಕಾರವು ಘೋಷಿಸಿದ ನೂತನ ಕೃಷಿ ಸಹಾಯಧನ ನೀತಿಯು ಗ್ರಾಮೀಣ ಪ್ರದೇಶಗಳಲ್ಲಿ ತೀವ್ರ ಪರಿಣಾಮ ಬೀರುತ್ತಿದೆ ಎಂದು ವರದಿಗಳು ತಿಳಿಸಿವೆ.

ಇಲಾಖೆಯ ಅಧಿಕೃತ ವರದಿಯ ಪ್ರಕಾರ ಕಳೆದ ತ್ರೈಮಾಸಿಕದಲ್ಲಿ 35% ರೈತರು ಈ ಸೌಲಭ್ಯವನ್ನು ಪಡೆದುಕೊಂಡಿದ್ದಾರೆ ಎಂದು ಹೇಳಲಾಗಿದೆ. ಆದರೆ ವಿರೋಧ ಪಕ್ಷದ ಮುಖಂಡರು ಇದು ಕೇವಲ ಪ್ರಚಾರಕ್ಕಾಗಿ ಮಾಡಲಾದ ಆಡಳಿತಾತ್ಮಕ ತಂತ್ರವೆಂದು ಆರೋಪಿಸಿದ್ದಾರೆ.

ನಿನ್ನೆ ನಡೆದ ತುರ್ತು ಸಭೆಯಲ್ಲಿ ಹೊಸ ಮಾರ್ಗಸೂಚಿಗಳನ್ನು ಪರಿಷ್ಕರಿಸಲು ಅಧಿಕಾರಿಗಳು ತೀರ್ಮಾನಿಸಿದ್ದಾರೆ. ಸಾರ್ವಜನಿಕರು ಈ ಮಾಹಿತಿಯ ಸತ್ಯಾಸತ್ಯತೆಯನ್ನು ಪರಿಶೀಲಿಸಬೇಕಾಗಿದೆ.`
    }
};

/** Switch between Paste Text and URL tabs */
function switchInputTab(mode) {
    const textSection = document.getElementById('textInputSection');
    const urlSection = document.getElementById('urlInputSection');
    const tabTextBtn = document.getElementById('tabTextBtn');
    const tabUrlBtn = document.getElementById('tabUrlBtn');
    const sourceTypeInput = document.getElementById('sourceTypeInput');

    if (!textSection || !urlSection) return;

    if (mode === 'url') {
        textSection.classList.add('hidden');
        urlSection.classList.remove('hidden');
        tabUrlBtn.classList.add('active');
        tabTextBtn.classList.remove('active');
        sourceTypeInput.value = 'url';
    } else {
        urlSection.classList.add('hidden');
        textSection.classList.remove('hidden');
        tabTextBtn.classList.add('active');
        tabUrlBtn.classList.remove('active');
        sourceTypeInput.value = 'text';
    }
}

/** Update live character counter */
function updateCharCount() {
    const textarea = document.getElementById('pastedText');
    const counter = document.getElementById('charCounter');
    if (!textarea || !counter) return;

    const count = textarea.value.length;
    counter.textContent = `${count.toLocaleString()} / 25,000 characters`;
    if (count > 25000) {
        counter.classList.add('text-danger');
    } else {
        counter.classList.remove('text-danger');
    }
}

/** Load pre-packaged sample news into input */
function loadSampleText(lang) {
    switchInputTab('text');
    const sample = DEMO_SAMPLES[lang];
    if (!sample) return;

    const titleInput = document.getElementById('customTitle');
    const textArea = document.getElementById('pastedText');
    const langSelect = document.getElementById('languageSelect');

    if (titleInput) titleInput.value = sample.title;
    if (textArea) {
        textArea.value = sample.text;
        updateCharCount();
    }
    if (langSelect) {
        langSelect.value = lang;
    }
}

/** Handle asynchronous analysis submission */
async function handleAnalysisSubmit(event) {
    event.preventDefault();

    const form = document.getElementById('analysisForm');
    const submitBtn = document.getElementById('analyzeSubmitBtn');
    const submitSpinner = document.getElementById('submitSpinner');
    const progressBox = document.getElementById('analysisProgressBox');
    const progressBar = document.getElementById('progressBarFill');
    const progressStatus = document.getElementById('progressStatusText');
    const errorBox = document.getElementById('formErrorMessage');

    const sourceType = document.getElementById('sourceTypeInput').value;
    const customTitle = (document.getElementById('customTitle') || {}).value || '';
    const selectedLanguage = (document.getElementById('languageSelect') || {}).value || 'auto';

    let contentInput = '';
    if (sourceType === 'url') {
        contentInput = (document.getElementById('articleUrl') || {}).value || '';
        if (!contentInput.trim()) {
            showError('Please enter a valid HTTP/HTTPS article URL.');
            return;
        }
    } else {
        contentInput = (document.getElementById('pastedText') || {}).value || '';
        if (contentInput.trim().length < 30) {
            showError('Please paste article text containing at least 30 characters.');
            return;
        }
    }

    // Hide error banner and show progress box
    errorBox.classList.add('hidden');
    progressBox.classList.remove('hidden');
    submitBtn.disabled = true;
    submitSpinner.classList.remove('hidden');

    // Simulate progressive milestones while awaiting server response
    let progress = 15;
    progressBar.style.width = '15%';
    progressStatus.textContent = 'Validating input parameters...';

    const progressTimer = setInterval(() => {
        if (progress < 85) {
            progress += 18;
            progressBar.style.width = `${progress}%`;
            if (progress >= 30 && progress < 50) {
                progressStatus.textContent = sourceType === 'url' ? 'Fetching article & parsing readable text...' : 'Validating linguistic structure...';
            } else if (progress >= 50 && progress < 70) {
                progressStatus.textContent = 'Evaluating persuasive writing & extracting factual claims...';
            } else if (progress >= 70) {
                progressStatus.textContent = 'Cross-referencing claims against reference evidence sources...';
            }
        }
    }, 600);

    try {
        const payload = {
            source_type: sourceType,
            content_input: contentInput,
            selected_language: selectedLanguage,
            custom_title: customTitle
        };

        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        clearInterval(progressTimer);
        const result = await response.json();

        if (response.ok && result.success) {
            progressBar.style.width = '100%';
            progressStatus.textContent = 'Analysis complete! Redirecting to report...';
            setTimeout(() => {
                window.location.href = result.redirect_url;
            }, 400);
        } else {
            progressBar.style.width = '0%';
            progressBox.classList.add('hidden');
            showError(result.error || 'Failed to complete analysis. Please check inputs and retry.');
            submitBtn.disabled = false;
            submitSpinner.classList.add('hidden');
        }
    } catch (err) {
        clearInterval(progressTimer);
        progressBox.classList.add('hidden');
        showError('Network or server connection failed. Ensure TruthLens is running on port 8765.');
        submitBtn.disabled = false;
        submitSpinner.classList.add('hidden');
    }
}

function showError(msg) {
    const errorBox = document.getElementById('formErrorMessage');
    if (errorBox) {
        errorBox.textContent = msg;
        errorBox.classList.remove('hidden');
    } else {
        alert(msg);
    }
}

/** Deletion confirmation modal management */
let pendingDeleteId = null;
let pendingDeleteRow = null;

function confirmDeleteHistoryRecord(id, title) {
    pendingDeleteId = id;
    pendingDeleteRow = document.getElementById(`row-${id}`);

    const modal = document.getElementById('deleteModal');
    const msg = document.getElementById('deleteModalMessage');
    const confirmBtn = document.getElementById('confirmDeleteBtn');

    if (msg) msg.textContent = `Are you sure you want to delete the record for "${title}"? This cannot be undone.`;
    if (confirmBtn) {
        confirmBtn.onclick = executeDeleteRecord;
    }
    if (modal) modal.classList.remove('hidden');
}

function confirmDeleteReport(id) {
    if (confirm('Are you sure you want to delete this analysis report and all associated claims?')) {
        fetch(`/api/history/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/history';
                } else {
                    alert(data.error || 'Deletion failed.');
                }
            })
            .catch(() => alert('Network error during deletion.'));
    }
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) modal.classList.add('hidden');
    pendingDeleteId = null;
    pendingDeleteRow = null;
}

async function executeDeleteRecord() {
    if (!pendingDeleteId) return;

    try {
        const response = await fetch(`/api/history/${pendingDeleteId}`, { method: 'DELETE' });
        const data = await response.json();
        if (response.ok && data.success) {
            if (pendingDeleteRow) {
                pendingDeleteRow.remove();
            }
            closeDeleteModal();
        } else {
            alert(data.error || 'Failed to delete record.');
        }
    } catch (err) {
        alert('Network connection error while deleting record.');
    }
}

/** Test AI API connection from Settings page */
async function testGeminiConnection() {
    const btn = document.getElementById('testApiBtn');
    const spinner = document.getElementById('testApiSpinner');
    const resultBox = document.getElementById('testResultBox');

    btn.disabled = true;
    spinner.classList.remove('hidden');
    resultBox.classList.add('hidden');

    try {
        const response = await fetch('/api/test-connection', { method: 'POST' });
        const data = await response.json();

        resultBox.classList.remove('hidden');
        if (data.success) {
            resultBox.className = 'test-result-box alert-success';
            resultBox.innerHTML = `<strong>Status: Connected</strong><br>${data.message}`;
        } else {
            resultBox.className = 'test-result-box alert-danger';
            resultBox.innerHTML = `<strong>Status: Error</strong><br>${data.error}`;
        }
    } catch (err) {
        resultBox.classList.remove('hidden');
        resultBox.className = 'test-result-box alert-danger';
        resultBox.innerHTML = `<strong>Error:</strong> Failed to reach server endpoint.`;
    } finally {
        btn.disabled = false;
        spinner.classList.add('hidden');
    }
}

/** Export analysis record as JSON */
function exportAnalysisJson(analysisId) {
    window.open(`/results/${analysisId}?format=json`, '_blank');
}
