plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "1.9.21"
    id("org.jetbrains.intellij") version "1.16.1"
}

group = "dev.spectra"
version = "0.1.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.google.code.gson:gson:2.10.1")
}

intellij {
    version.set("2023.3")
    type.set("IC") // IntelliJ IDEA Community Edition

    plugins.set(listOf(
        "org.intellij.plugins.markdown"
    ))
}

tasks {
    withType<JavaCompile> {
        sourceCompatibility = "17"
        targetCompatibility = "17"
    }

    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        kotlinOptions.jvmTarget = "17"
    }

    patchPluginXml {
        sinceBuild.set("233")
        untilBuild.set("243.*")

        pluginDescription.set("""
            <h2>Spectra - User Story Management</h2>
            <p>IDE integration for Spectra markdown-based user story management.</p>

            <h3>Features</h3>
            <ul>
                <li>Syntax highlighting for Spectra markdown</li>
                <li>Code completion for status, priority, and tracker IDs</li>
                <li>Quick navigation to epic/story definitions</li>
                <li>Real-time validation inspections</li>
                <li>Quick fixes for common issues</li>
                <li>Tool window with sync status and stories</li>
                <li>External tool integration with Spectra CLI</li>
            </ul>

            <h3>Requirements</h3>
            <ul>
                <li>Spectra CLI installed (<code>pip install spectra</code>)</li>
            </ul>
        """.trimIndent())

        changeNotes.set("""
            <h3>0.1.0</h3>
            <ul>
                <li>Initial release</li>
                <li>Basic syntax highlighting</li>
                <li>Validation inspections</li>
                <li>Code completion</li>
                <li>Tool window</li>
            </ul>
        """.trimIndent())
    }

    signPlugin {
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        token.set(System.getenv("PUBLISH_TOKEN"))
    }

    runIde {
        autoReloadPlugins.set(true)
    }
}
