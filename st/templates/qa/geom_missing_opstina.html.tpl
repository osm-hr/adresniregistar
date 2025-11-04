{% extends "base.html.tpl" %}
{% block body %}

<iframe id="hiddenIframe" name="hiddenIframe"></iframe>

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
        Na ovom izveštaju se nalazi sve ulice kojima se geometrije u RGZ-u i u OSM-u ne poklapaju. Izveštaj sadrži dve tabele i objašnjeno je na samoj strani detaljno šta one predstavljaju.
        Detaljna objašnjenja kolona u tabelama:
		<ul>
		    <li><b>Naselje</b> &mdash; Naselje kojem pripada ulica. Klik na naselje vodi do izveštaja za sve ulice u tom naselju.</li>
			<li><b>Id (RGZ)</b> &mdash; Identifikator ulice u RGZ-u (ono što se stavlja u „ref:RS:ulica” tag).
			Možete da filtrirate po tipu ulice, a dublje objašnjenje kako se formira identifikator možete da vidite <a href="https://community.openstreetmap.org/t/topic/9338/14" target="_blank">ovde na forumu</a>.</li>
			<li><b>Ulica (RGZ)</b> &mdash; Ime ulice iz RGZ-a, a posle strelice i pravilno ime ulice kako treba uneti u OSM.
			Ukoliko nema imena ulice posle strelice, znači da ulice još nema u <a href="https://dina.openstreetmap.rs/ar/street_mapping.html" target="_blank">registru</a>.
			Klikom na ulicu se otvara geojson.io portal na kome može da se vidi i RGZ ulica (crvenom bojom) i sve conflated OSM ulice (plavom bojom).
			Ukoliko na početku ulice ima simbol „⭕”, algoritam je detektovao da je u pitanju zaseok, tj. virtuelna ulica (ne postoji fizički put). Ovo su ulice koje ne treba da se unose.
			</li>
			<li><b>Dužina (RGZ)</b> &mdash; Ukupna dužina ulice u RGZ-u (u metrima)</li>
			<li><b>Ukupna dužina potencijalnih puteva</b> &mdash; Ukupna dužina onog dela svih potencijalnih kandidata segmenata kojima se OSM geometrija poklapa sa geometrijom iz RGZ-a. Dužina koja se računa je samo onaj deo OSM puta koji se poklapa sa RGZ geometrijom. Npr. ako je dužina puta 50m, a procenat poklapanja 80%, onda se računa 40m.</li>
			<li><b>Ukupna dužina puteva za iscrtati</b> &mdash; Ukupna dužina greške RGZ-a gde je možda potrebno ucrtati puteve</li>
			<li><b>Conflated putevi</b> &mdash; Spisak svih nađenih puteva u OSM-u koji su spojeni sa RGZ ulicom preko „ref:RS:ulica” taga.</li>
			<li><b>Potencijalni putevi (% poklapanja, dužina)</b> &mdash; Spisak svih potencijalno nađenih OSM puteva koje treba spojiti sa RGZ-om. Za svaki OSM put je naveden procenat poklapanja sa RGZ putem i njegova OSM dužina.
			Ukoliko je ime puta <s>precrtano</s>, to označava da se ime iz RGZ-a i ime iz OSM-a ne slažu. Ukoliko ime puta ima prefiks „✅”, to znači da se ime RGZ i OSM puta kompletno slažu. <b>PAŽNJA:</b> u ovoj koloni može biti dosta grešaka i ne unositi ovo automatizovano</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../../index.html">DINA</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../index.html">Ulice</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../qa.html">QA</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../geom_missing.html">Nedostajuće geometrije</a></li>
	<li class="breadcrumb-item active" aria-current="page">{{ opstina_name }}</li>
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
		$.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
		    let streetType = $("#streetTypeSelect option:selected").val();
		    let isConflated = $("#isConflatedSelect option:selected").val();
			let isPotential = $("#isPotentialSelect option:selected").val();

            let streetTypeFilter = true;
            if (streetType === 'street0') {
                streetTypeFilter = data[1][6] === "0";
            } else if (streetType === 'street1') {
                streetTypeFilter = data[1][6] === "1";
            } else if (streetType === 'street2') {
                streetTypeFilter = data[1][6] === "2";
            } else if (streetType === 'street3') {
                streetTypeFilter = data[1][6] === "3";
            }

            let isConflatedFilter = true;
            if (isConflated === 'yes') {
                isConflatedFilter = data[5].indexOf('w') > -1;
            } else if (isConflated === 'no') {
                isConflatedFilter = data[5].indexOf('w') === -1;
            }

            let isPotentialFilter = true;
            if (isPotential === 'yes') {
                isPotentialFilter = data[6].indexOf('✅') > -1;
            } else if (isPotential === 'partial') {
                isPotentialFilter = data[6].indexOf('(') > -1;
            } else if (isPotential === 'errors') {
                isPotentialFilter = data[6].indexOf('<s>') > -1;
            } else if (isPotential === 'no') {
                isPotentialFilter = data[6].trim() === '';
            }

			return streetTypeFilter && isConflatedFilter && isPotentialFilter;
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
		    order: [[4, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [3, 4], className: 'text-right' },
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
		    order: [[4, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [3, 4], className: 'text-right' },
		    ]
		});

        $('#streetTypeSelect').on('change', function() {
            tableConflate.draw();
            tableDrawing.draw();
        });
        $('#isConflatedSelect').on('change', function() {
            tableConflate.draw();
            tableDrawing.draw();
        });
        $('#isPotentialSelect').on('change', function() {
            tableConflate.draw();
            tableDrawing.draw();
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


<h2>Izveštaj nedostajućih geometrija za {{ opstina_name }}</h2>
<br/>

<p>Ovde možete videti sve ulice unutar opštine „{{ opstina_name }}” kojima se geometrije u RGZ-u i u OSM-u ne poklapaju. Razlikujemo dva slučaja:
<ul>
    <li>
        <b>Potrebna konflacija</b> &mdash; OSM ima kandidate ulice, ali nisu povezane. U ovom slučaju treba prosto povezati te ulice ukoliko je to moguće
    </li>
    <li>
        <b>Potrebno crtanje</b> &mdash; U OSM-u nema ulice. U ovom slučaju proveriti zašto se ovo dešava:
        <ul>
            <li>Može biti da je RGZ geometrija skroz pogrešna i tad ne treba raditi ništa</li>
            <li>Može biti da je postoji OSM ulica, ali da je bila predugačka i analiza je nije razmatrala. Tad treba preseći ulicu i povezati samo njen deo</li>
            <li>Može biti da ne postoji OSM put i da ga treba ucrtati i povezati</li>
        </ul>
    </li>
</ul>

<p>
<b>Kliknite na <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a></b> u gornjem meniju da razumete kako da tumačite kolone u ovoj tabeli.
</p>

<div class="text-right">
    <label for="streetType">Tip ulice</label>
    <select name="streetType" id="streetTypeSelect">
      <option value="all"></option>
      <option value="street0">Ulica u naseljenom mestu sa uličnim sistemom</option>
      <option value="street1">Trg u naseljenom mestu sa uličnim sistemom</option>
      <option value="street2">Zaseok u naseljenom mestu bez uličnog sistema</option>
      <option value="street3">Ulica u naseljenom mestu bez uličnog sistema</option>
    </select>
    <br/>
    <label for="isConflated">Conflated putevi</label>
    <select name="isConflated" id="isConflatedSelect">
      <option value="all"></option>
      <option value="yes">Da</option>
      <option value="no">Ne</option>
    </select>
    <br/>
    <label for="isPotential">Potencijalni putevi</label>
    <select name="isPotential" id="isPotentialSelect">
      <option value="all"></option>
      <option value="yes">Bar jedno kompletno slaganje </option>
      <option value="partial">Bar jedan potencijalni put</option>
      <option value="errors">Bar jedna precrtana ulica</option>
      <option value="no">Bez potencijalnih puteva</option>
    </select>
</div>

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
            <td><a href="../opstine/{{ opstina_name_norm }}/{{ street.rgz_naselje }}.html">{{ street.rgz_naselje }}</a></td>
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
      <tfoot>
        <tr>
            <th>TOTAL:</th>
            <th class="d-sm-table-cell"></th>
            <th class="d-sm-table-cell"></th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total_opstina_need_conflate.rgz_way_length / 1000.0).replace('.', ',') }}km</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total_opstina_need_conflate.geom_missing_need_conflate_length / 1000.0).replace('.', ',') }}km</th>
            <th class="d-sm-table-cell"></th>
            <th class="d-sm-table-cell"></th>
        </tr>
      </tfoot>
    </table>
  </div>
  <div class="tab-pane fade" id="pills-by-drawing" role="tabpanel" aria-labelledby="pills-by-drawing-tab">
    <table id="list-drawing" class="table table-sm table-striped table-bordered table-hover w-100">
      <thead class="thead-dark sticky-top">
        <tr>
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
            <td><a href="../opstine/{{ opstina_name_norm }}/{{ street.rgz_naselje }}.html">{{ street.rgz_naselje }}</a></td>
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
      <tfoot>
        <tr>
            <th>TOTAL:</th>
            <th class="d-sm-table-cell"></th>
            <th class="d-sm-table-cell"></th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total_opstina_need_drawing.rgz_way_length / 1000.0).replace('.', ',') }}km</th>
            <th class="d-sm-table-cell">{{ '{0:0.2f}'.format(total_opstina_need_drawing.geom_missing_need_drawing_length / 1000.0).replace('.', ',') }}km</th>
            <th class="d-sm-table-cell"></th>
            <th class="d-sm-table-cell"></th>
        </tr>
      </tfoot>
    </table>
  </div>
</div>

{% endblock %}