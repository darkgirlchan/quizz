// Manejo del cuestionario
document.addEventListener('DOMContentLoaded', function() {
    const options = document.querySelectorAll('.option');
    const nextBtn = document.getElementById('next-btn');
    const powerButtons = document.querySelectorAll('.power-btn');
    
    // Selección de respuesta
    options.forEach(option => {
        option.addEventListener('click', function() {
            options.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            nextBtn.disabled = false;
        });
    });
    
    // Botón siguiente
    nextBtn.addEventListener('click', function() {
        const selectedOption = document.querySelector('.option.selected');
        if (!selectedOption) return;
        
        const answer = selectedOption.dataset.value;
        
        // Enviar respuesta al servidor
        fetch('/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ answer: answer })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.next_url;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    // Uso de poderes
    powerButtons.forEach(button => {
        button.addEventListener('click', function() {
            const powerId = this.dataset.powerId;
            const uses = parseInt(this.dataset.uses);
            
            if (uses <= 0) {
                alert('No te quedan usos de este poder');
                return;
            }
            
            // Obtener el ID de la pregunta actual de la URL
            const urlParams = new URLSearchParams(window.location.search);
            const questionId = parseInt(urlParams.get('q')) || 0;
            
            // Usar poder
            usePower(powerId, questionId);
        });
    });
});

// Función para usar poderes
function usePower(powerId, questionId) {
    fetch('/use_power', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            power_id: powerId,
            question_id: questionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Ejecutar efecto del poder
            switch(powerId) {
                case 'corrector':
                    if (data.correct_answer) {
                        // Resaltar la respuesta correcta
                        const options = document.querySelectorAll('.option');
                        options.forEach(option => {
                            if (option.dataset.value === data.correct_answer) {
                                option.style.backgroundColor = '#d4edda';
                                option.style.borderColor = '#c3e6cb';
                            }
                        });
                    }
                    break;
                    
                case 'fifty':
                    if (data.remove_options) {
                        // Ocultar opciones incorrectas
                        const options = document.querySelectorAll('.option');
                        options.forEach(option => {
                            if (data.remove_options.includes(option.dataset.value)) {
                                option.style.display = 'none';
                            }
                        });
                    }
                    break;
                    
                case 'double':
                    // Marcar para doble puntuación (se maneja en el backend)
                    alert('Esta pregunta tendrá doble puntuación');
                    break;
                    
                case 'skip':
                    // Saltar pregunta
                    if (data.skip) {
                        window.location.reload();
                    }
                    break;
                    
                case 'time':
                    // Añadir tiempo extra (implementar si hay temporizador)
                    if (data.extra_time) {
                        alert(`Se han añadido ${data.extra_time} segundos extra`);
                    }
                    break;
            }
            
            // Actualizar contador de usos
            const powerBtn = document.querySelector(`[data-power-id="${powerId}"]`);
            const currentUses = parseInt(powerBtn.dataset.uses);
            powerBtn.dataset.uses = currentUses - 1;
            powerBtn.querySelector('.power-uses').textContent = `(${currentUses - 1} usos)`;
            
            if (currentUses - 1 <= 0) {
                powerBtn.disabled = true;
            }
        } else {
            alert('Error al usar el poder: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}