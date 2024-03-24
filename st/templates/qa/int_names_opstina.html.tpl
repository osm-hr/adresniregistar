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
            <ul>
                <li><b>OSM ulica</b> &mdash; Ime ulice i link na OSM way</li>
                <li><b>„ref:RS:ulica” tag</b> &mdash; Označava da li je ulica spojena sa RGZ-om preko „ref:RS:ulica” taga. Ukoliko jeste, koristi se RGZ ime da se zaključi vrednost „int_name” taga</li>
                <li><b>Pogrešan „int_name” tag</b> &mdash; Tag postoji, ali mislimo da je pogrešan. U nastavku su navedene trenutna vrednost taga i (posle strelice) šta bi trebalo da bude vrednost tog taga</li>
                <li><b>Nedostaje „int_name” tag</b> &mdash; Na ovom OSM way-u nema „int_name” taga. U nastavku je navedena vrednost taga koji treba da se stavi</li>
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
    <li class="breadcrumb-item" aria-current="page"><a href="../../index.html">DINA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../index.html">Ulice</a></li>
	<li class="breadcrumb-item" aria-current="page"><a href="../qa.html">QA</a></li>
    <li class="breadcrumb-item" aria-current="page"><a href="../int_names.html">Int nazivi ulica</a></li>
    <li class="breadcrumb-item" aria-current="page">{{ opstina_name }}</li>
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
		    let refExists = $("#refExistsSelect option:selected").val();
			let errorType = $("#errorTypeSelect option:selected").val();

            let refExistsFilter = true;
            if (refExists === 'yes') {
                refExistsFilter = data[1].indexOf('✅') > -1;
            } else if (errorType === 'no') {
                refExistsFilter = data[1].indexOf('❌') > -1;
            }

            let errorTypeFilter = true;
            if (errorType === 'wrong_int_name') {
                errorTypeFilter = data[2].indexOf('❌') > -1;
            } else if (errorType === 'missing_int_name') {
                errorTypeFilter = data[3].indexOf('⚠') > -1;
            }

			return refExistsFilter && errorTypeFilter;
		});

	    var table = $('#list').DataTable({
		    stateSave: true,
		    order: [[0, 'desc']],
		    lengthMenu: [ [10, 50, -1], [10, 50, "All"] ],
		    columnDefs: [
		        { targets: [2, 3], className: 'text-right' },
		    ],
            "columns": [
                null,
                { "width": "5%" },
                null,
                null
              ]
		});

        $('#refExistsSelect').on('change', function() {
            table.draw();
        });
        $('#errorTypeSelect').on('change', function() {
            table.draw();
        });
	} );
    </script>

<h2>Int nazivi ulica</h2>
<br/>
<p>Ovde možete da vidite potencijalne probleme sa „int_name” tagom za ulice u OpenStreetMap-apa za opštinu „{{ opstina_name }}”. Moguće je da „int_name” tag fali, a moguće je i da je pogrešan.
    <br/>
    Savetujemo da pročitate <a href="" data-toggle="modal" data-target="#exampleModal">„Pomoć”</a> u gornjem meniju da bolje razumete kako da tumačite tabelu.
    U gornjem desnom uglu je filtriranje.
</p>
<br/>
<br/>

<div class="text-right">
    <label for="errorType">Postoji ref:RS:ulica tag:</label>
    <select name="refExists" id="refExistsSelect">
      <option value="all"></option>
      <option value="yes">Da</option>
      <option value="no">Ne</option>
    </select>
    <br/>
    <label for="errorType">Tip greške:</label>
    <select name="errorType" id="errorTypeSelect">
      <option value="all">Sve</option>
      <option value="wrong_int_name">Samo pogrešan tag</option>
      <option value="missing_int_name">Samo nedostajući tag</option>
    </select>
</div>

<table id="list" class="table table-sm table-striped table-bordered table-hover w-75">
<thead class="thead-dark sticky-top">
	<tr>
		<th>OSM ulica</th>
		<th>„ref:RS:ulica” tag</th>
        <th>Pogrešan „int_name” tag</th>
        <th>Nedostaje „int_name” tag</th>
	</tr>
</thead>
<tbody>
	{% for street in streets %}
	<tr>
		<td><a href="{{ street.osm_link }}" target="_blank">{{ street.osm_name }}</a></td>
		<td>{% if street.has_ref_rs_ulica %}✅{% else %}❌{% endif %}</td>
        <td>
            {% if street.wrong_int_name %}
            ❌ {{ street.osm_int_name }} ➝ {{ street.osm_int_name_proper }}
            {% endif %}
        </td>
        <td>
            {% if street.missing_int_name %}
            ⚠️ {{ street.osm_int_name_proper }}
            {% endif %}
        </td>
	</tr>
	{% endfor %}
</tbody>
</table>

{% endblock %}