/* =========================
   FOOTER YEAR
========================= */

const year = document.getElementById("year");

if (year) {
  year.textContent = new Date().getFullYear();
}


/* =========================
   WRITING FILTER
========================= */

const filterButtons = document.querySelectorAll(".filter-button");
const archiveItems = document.querySelectorAll(".archive-item");


if (filterButtons.length > 0 && archiveItems.length > 0) {

  filterButtons.forEach((button) => {

    button.addEventListener("click", () => {

      const selectedFilter = button.dataset.filter;


      /* Update active button */

      filterButtons.forEach((btn) => {
        btn.classList.remove("active");
      });

      button.classList.add("active");


      /* Filter articles */

      archiveItems.forEach((item) => {

        const category = item.dataset.category;

        if (
          selectedFilter === "all" ||
          category === selectedFilter
        ) {
          item.classList.remove("hidden");
        }

        else {
          item.classList.add("hidden");
        }

      });

    });

  });

}