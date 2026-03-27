<script>
  import Phone from './components/Phone.svelte';
  import Site from './components/Site.svelte';
</script>

<main>
  <Phone />
  <Site />
</main>

<style>
  :global(*, *::before, *::after) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(
      135deg,
      #4a90d9 0%,
      #357abd 30%,
      #2968a8 70%,
      #1a5694 100%
    );
    min-height: 100vh;
  }

  main {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 30px 20px;
    gap: 40px;
    min-height: 100vh;
  }

  @media (max-width: 900px) {
    main {
      flex-direction: column;
      align-items: center;
    }
  }
</style>
