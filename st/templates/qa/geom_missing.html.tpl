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
	<li class="breadcrumb-item" aria-current="page">Nedostajuće geometrije</li>
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
		        { targets: [1, 2, 3, 4], className: 'text-right' },
		    ]
		});
	    var tableConflate = $('#list-conflate').DataTable({
		    stateSave: true,
		    stateDuration: 0,
			stateSaveCallback: function (settings, data) {
				localStorage.setItem('DataTables_st_naselje', JSON.stringify(data));
			},
			stateLoadCallback: function (settings) {
				return JSON.parse(localStorage.getItem('DataTables_st_naselje'));
			},
		    order: [[5, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [4, 5], className: 'text-right' },
		    ]
		});
	    var tableDrawing = $('#list-drawing').DataTable({
		    stateSave: true,
		    stateDuration: 0,
			stateSaveCallback: function (settings, data) {
				localStorage.setItem('DataTables_st_naselje2', JSON.stringify(data));
			},
			stateLoadCallback: function (settings) {
				return JSON.parse(localStorage.getItem('DataTables_st_naselje2'));
			},
		    order: [[5, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [4, 5], className: 'text-right' },
		    ]
		});

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
    } );
    </script>

<h2>Nedostajuće geometrije ulica</h2>
<br/>
<p>Ovde možete videti sve ulice kojima se geometrije u RGZ-u i u OSM-u ne poklapaju. Razlikujemo dva slučaja:
<ul>
    <li>
        <b>Potrebna konflacija</b> &mdash; OSM ima kandidate ulice, ali nisu povezane.
    </li>
    <li>
        <b>Potrebno crtanje</b> &mdash; U OSM-u nema ulice, pa je možda potrebno da je ucrtamo.
    </li>
</ul>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-50">
<thead class="thead-dark sticky-top">
	<tr>
		<th>Opština</th>
		<th>Potrebna konflacija (broj ulica)</th>
		<th>Potrebna konflacija (dužina)</th>
		<th>Potrebno crtanje (broj ulica)</th>
		<th>Potrebno crtanje (dužina)</th>
	</tr>
</thead>
<tbody>
	{% for opstina in opstine %}
	<tr>
		<td><a href="geom_missing/{{ opstina.name }}.html">{{ opstina.name }}</a></td>
		<td>{{ opstina.geom_missing_need_conflate_count }}</td>
		<td data-order="{{ opstina.geom_missing_need_conflate_length }}">{{ '{0:0.2f}'.format(opstina.geom_missing_need_conflate_length / 1000.0).replace('.', ',') }}km</td>
		<td>{{ opstina.geom_missing_need_drawing_count }}</td>
		<td data-order="{{ opstina.geom_missing_need_drawing_length }}">{{ '{0:0.2f}'.format(opstina.geom_missing_need_drawing_length / 1000.0).replace('.', ',') }}km</td>
	</tr>
	{% endfor %}
</tbody>
<tfoot>
	<tr>
		<th>Serbia TOTAL:</th>
		<th class="d-sm-table-cell">{{ total.geom_missing_need_conflate_count }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total.geom_missing_need_conflate_length / 1000.0).replace('.', ',') }}km</th>
		<th class="d-sm-table-cell">{{ total.geom_missing_need_drawing_count }}</th>
		<th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total.geom_missing_need_drawing_length / 1000.0).replace('.', ',') }}km</th>
	</tr>
</tfoot>
</table>

<br/><br/>
<h3>Top 100 ulica sa najvećom dužinom nedostajućih ulica</h3>


<ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
  <li class="nav-item" role="presentation">
    <button class="nav-link active" id="pills-by-conflate-tab" data-toggle="pill" data-target="#pills-by-conflate" type="button" role="tab" aria-controls="pills-by-conflate" aria-selected="true">Potrebna konflacija</button>
  </li>
  <li class="nav-item" role="presentation">
    <button class="nav-link" id="pills-by-drawing-tab" data-toggle="pill" data-target="#pills-by-drawing" type="button" role="tab" aria-controls="pills-by-drawing" aria-selected="false">Potrebno crtanje</button>
  </li>
</ul>

<div class="tab-content" id="pills-tabContent">
  <div class="tab-pane fade show active" id="pills-by-conflate" role="tabpanel" aria-labelledby="pills-by-conflate-tab">
    <table id="list-conflate" class="table table-sm table-striped table-bordered table-hover w-100">
      <thead class="thead-dark sticky-top">
        <tr>
            <th>Opština</th>
            <th>Naselje</th>
            <th>Id (RGZ)</th>
            <th>Ulica (RGZ)</th>
            <th>Dužina (RGZ)</th>
            <th>Ukupna dužina potencijalnih puteva</th>
            <th>Conflated putevi</th>
            <th>Potencijalni putevi (% poklapanja, dužina)</th>
        </tr>
      </thead>
      <tbody>
        {% for street in streets_need_conflate %}
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
            <td data-order="{% if street.is_zaseok %}-1{% else %}{{ street.geom_missing_need_conflate }}{% endif %}">{% if not street.is_zaseok %}{{ '{0:0.2f}'.format(street.geom_missing_need_conflate).replace('.', ',') }}m{% endif %}</td>
            <td data-order="{{ street.conflated_osm_way_length_sum }}">
                {% if street.conflated_ways|length > 0 %}
                <ul>
                {% for conflated_way in street.conflated_ways %}
                    <li><a href="{{ conflated_way.osm_link }}" target="_blank">{{ conflated_way.osm_id }}</a></li>
                {% endfor %}
                </ul>
                {% endif %}
            </td>
            <td data-order="{{ street.geom_missing_need_conflate }}">
                {% if street.found_ways|length > 0 %}
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
  </div>
  <div class="tab-pane fade" id="pills-by-drawing" role="tabpanel" aria-labelledby="pills-by-drawing-tab">
    <table id="list-drawing" class="table table-sm table-striped table-bordered table-hover w-100">
      <thead class="thead-dark sticky-top">
        <tr>
            <th>Opština</th>
            <th>Naselje</th>
            <th>Id (RGZ)</th>
            <th>Ulica (RGZ)</th>
            <th>Dužina (RGZ)</th>
            <th>Ukupna dužina puteva za iscrtati</th>
            <th>Conflated putevi</th>
            <th>Potencijalni putevi (% poklapanja, dužina)</th>
        </tr>
      </thead>
      <tbody>
        {% for street in streets_need_drawing %}
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
            <td data-order="{% if street.is_zaseok %}-1{% else %}{{ street.geom_missing_need_drawing }}{% endif %}">{% if not street.is_zaseok %}{{ '{0:0.2f}'.format(street.geom_missing_need_drawing).replace('.', ',') }}m{% endif %}</td>
            <td data-order="{{ street.conflated_osm_way_length_sum }}">
                {% if street.conflated_ways|length > 0 %}
                <ul>
                {% for conflated_way in street.conflated_ways %}
                    <li><a href="{{ conflated_way.osm_link }}" target="_blank">{{ conflated_way.osm_id }}</a></li>
                {% endfor %}
                </ul>
                {% endif %}
            </td>
            <td data-order="{{ street.geom_missing_need_drawing }}">
                {% if street.found_ways|length > 0 %}
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
  </div>
</div>

{% endblock %}