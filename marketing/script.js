const planPrices = {
  50: 0.99,
  200: 2.99,
  2000: 9.99,
};

function calculateOverspend(storageGb, services) {
  const monthly = planPrices[String(storageGb)] || 0;
  const serviceMultiplier = Math.max(services.length, 1);
  const recoverableRate = storageGb >= 2000 ? 0.28 : storageGb >= 200 ? 0.22 : 0.16;
  return Math.max(monthly * serviceMultiplier * recoverableRate, 0.01);
}

function updateCalculator() {
  const storage = document.querySelector("#storage-plan").value;
  const services = [...document.querySelectorAll("input[name='service']:checked")].map((item) => item.value);
  const monthlyOverspend = calculateOverspend(storage, services);
  document.querySelector("#savings-output").textContent =
    `Estimated storage pressure to review: $${monthlyOverspend.toFixed(2)}/month. Scan locally before changing storage plans.`;
}

async function loadStars() {
  try {
    const response = await fetch("https://api.github.com/repos/gokulrajanpillai/CloudSaver");
    const data = await response.json();
    document.querySelector("#star-count").textContent = `${data.stargazers_count || 0} GitHub stars`;
  } catch {
    document.querySelector("#star-count").textContent = "Open source on GitHub";
  }
}

document.querySelector("#storage-plan").addEventListener("change", updateCalculator);
document.querySelectorAll("input[name='service']").forEach((input) => {
  input.addEventListener("change", updateCalculator);
});

updateCalculator();
loadStars();
