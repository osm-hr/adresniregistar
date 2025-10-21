{% extends "base.html.tpl" %}
{% block body %}

<!-- Modal -->
<div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="exampleModalLabel">Značenje kolona</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        Ovaj izveštaj proverava da li u blizini ulice ima nepovezana ulica sa sličnom geometrijom i pogrešnim imenom ulice. Potrebno je proveriti zašto se ovo dešava:
        <ul>
            <li>Može biti da je ime slično i da ga treba izmeniti da odgovora pravom imenu ulice i uraditi konflaciju ulice</li>
            <li>Takođe je moguće da je to neka dodatna ulica koja nije povezana sa RGZ-om (nema „<code>ref:RS:ulica</code>” tag), pa onda treba naći odgovaraju ulicu u RGZ-u i povezati je</li>
            <li>Treći scenario je da ovakva ulica uopšte ne postoji u RGZ-u i onda treba obrisati ime ove ulice u OSM-u skroz</li>
        </ul>
        <br><br>
        Kolone u tabeli:
		<ul>
			<li><b>Opština</b> &mdash; Opština analize</li>
			<li><b># pogrešnih imena”</b> &mdash; Ukupan broj segmenata ulice kojima je ime pogrešno</li>
			<li><b>Dužina pogrešnih imena”</b> &mdash; Ukupna dužina svih segmenata ulice. Za dužinu segmenta se ne uzima celokupna dužina iz OSM-a nego samo onaj deo koji je u geometrijski poklopljen sa geometrijom RGZ ulice</li>
		</ul>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Zatvori</button>
      </div>
    </div>
  </div>
</div>

<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item" aria-current="page"><a href="../index.html">DINA</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="index.html">Ulice</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="qa.html">QA</a></li>
	<li class="breadcrumb-item" aria-current="page">Neslaganje imena</li>
  </ol>
</nav>
    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js" crossorigin="anonymous"></script>
    <script>
	$(document).ready( function () {
	    $('#list').DataTable({
		    stateSave: true,
		    stateDuration: 0,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [1, 2], className: 'text-right' },
		    ]
		});
        $('#list2').DataTable({
		    stateSave: true,
		    stateDuration: 0,
		    order: [[0, 'asc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [1, 2], className: 'text-right' },
		    ]
		});
	} );

	function copyToClipboard(text, messageId) {
        // Create a temporary textarea element to copy from
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);

        // Select and copy the text
        textarea.select();
        document.execCommand('copy');

        // Remove the temporary element
        document.body.removeChild(textarea);

        // Show success message
        const message = document.getElementById('success-message-' + messageId);
        message.classList.add('show-message');

        // Hide the message after 2 seconds
        setTimeout(() => {
            message.classList.remove('show-message');
        }, 2000);
    }
    </script>

<h2>Neslaganje imena ulica</h2>
<br/>
<p>Ovde možete da vidite sve ulice preko čije geometrije prelazi ulica sa različitim imenom (i ta ulica nije povezana preko <code>ref:RS:ulica</code> taga sa RGZ ulicama. To znači da ulica nije dobro povezana, ili da u blizini ima druga ulica koja nije dobro povezana.
    Klikom na opštinu dobijate detaljnije podatke za tu opštinu. U gornjem desnom uglu je filtriranje.
    <br/>
    <br/>
    Da biste bolje razumeli značenje kolona u tabeli, pogledajte <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a>.
</p>
<br/>
<br/>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th># pogrešnih imena</th>
		<th>Dužina pogrešnih imena</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="name_mismatch/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.name_mismatch_segment_count }}</td>
		<td data-order="{{ opstina.name_mismatch_length }}">{{ '{0:0.2f}'.format(opstina.name_mismatch_length / 1000.0).replace('.', ',') }}km</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.name_mismatch_segment_count }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total.name_mismatch_length / 1000.0).replace('.', ',') }}km</th>
	</tr>
</tfoot>
</table>

<br/><br/>
<h3>Top 100 ulica sa najvećom dužinom neslaganja</h3>

<table id="list2" class="table table-sm table-striped table-bordered table-hover w-100">
<thead class="thead-dark sticky-top">
	<tr>
	    <th>Opština</th>
	    <th>Naselje</th>
		<th>Id (RGZ)</th>
		<th>Ulica (RGZ)</th>
		<th>Dužina (RGZ)</th>
		<th>Broj neslaganja</th>
		<th>Relativna dužina neslaganja</th>
		<th>Conflated putevi</th>
		<th>Potencijalni putevi (% poklapanja, dužina)</th>
	</tr>
</thead>
<tbody>
    {% for street in streets %}
    <tr>
        <td><a href="opstine/{{ street.rgz_opstina }}.html">{{ street.rgz_opstina }}</a></td>
        <td><a href="opstine/{{ street.rgz_opstina_norm }}/{{ street.rgz_naselje }}.html">{{ street.rgz_naselje }}</a></td>
        <td>{{ street.rgz_ulica_mb }}</td>
        <td>{% if street.is_zaseok %}⭕ {% endif %}<a href="{{ street.rgz_geojson_url }}" target="_blank">{{ street.rgz_ulica }}</a> {% if street.rgz_ulica_proper != '' %} ➝ {{ street.rgz_ulica_proper }}{% endif %}
        {% if street.copy_text %}
        <span class="tooltip-container">
            <svg class="copy-icon" onclick="copyToClipboard('{{ street.copy_text}}', '{{ street.rgz_ulica_mb }}')" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg><span id="success-message-{{ street.rgz_ulica_mb }}" class="success-message">Kopirano!</span>
        </span>
        {% endif %}
        </td>
        <td data-order="{{ street.rgz_way_length }}">{{ street.rgz_way_length }}m</td>
        <td data-order="{{ street.found_way_name_mismatch_count }}">{{ street.found_way_name_mismatch_count }}</td>
        <td data-order="{{ street.found_way_name_mismatch_length }}">{{ '{0:0.2f}'.format(street.found_way_name_mismatch_length).replace('.', ',') }}m</td>
        <td data-order="{{ street.conflated_osm_way_length_sum }}">
            {% if street.conflated_ways|length > 0 %}
            <ul>
            {% for conflated_way in street.conflated_ways %}
                <li><a href="{{ conflated_way.osm_link }}" target="_blank">{{ conflated_way.osm_id }}</a></li>
            {% endfor %}
            </ul>
            {% endif %}
        </td>
        <td data-order="{{ street.found_way_name_mismatch_length }}">
            {% if street.found_ways|length > 0 %}
            <br/>
            <ul>
            {% for found_way in street.found_ways %}
                <li>
                    <a href="{{ found_way.osm_link }}" target="_blank">
                        {% if found_way.name_match %}
                        ✅
                        {% elif found_way.norm_name_match %}
                        ⚠️
                        {% endif %}
                        {% if found_way.wrong_name %}
                        <s>
                        {% endif %}
                        {{ found_way.osm_name }}
                        {% if found_way.wrong_name %}
                        </s>
                        {% endif %}
                    </a>
                    ({{ found_way.found_intersection }}%, {{ found_way.found_osm_way_length }}m)
                </li>
            {% endfor %}
            </ul>
            {% endif %}
        </td>
    </tr>
    {% endfor %}
</tbody>
</table>

{% endblock %}