// Copyright Southern Spear. All Rights Reserved.

#include "SSSettingsWidget.h"

#include "Components/BackgroundBlur.h"
#include "Components/ScrollBox.h"
#include "GameFramework/GameUserSettings.h"
#include "Kismet/KismetSystemLibrary.h"
#include "SSUserPrefs.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	const int32 FrameLimits[] = { 30, 60, 90, 120, 144, 165, 240, 0 };
	const EWindowMode::Type WindowModes[] = { EWindowMode::Fullscreen, EWindowMode::WindowedFullscreen, EWindowMode::Windowed };

	UGameUserSettings* Settings() { return GEngine ? GEngine->GetGameUserSettings() : nullptr; }

	UButton* ArrowButton(UWidgetTree* T, const TCHAR* Glyph)
	{
		UButton* Button = T->ConstructWidget<UButton>();
		FButtonStyle Style = Button->GetStyle();
		auto Flat = [](const FLinearColor& C) { FSlateBrush B; B.DrawAs = ESlateBrushDrawType::Box; B.TintColor = FSlateColor(C); return B; };
		Style.SetNormal(Flat(SSPalette::Field700(0.9f)));
		Style.SetHovered(Flat(SSPalette::Brass500(0.95f)));
		Style.SetPressed(Flat(SSPalette::Brass300()));
		Style.SetNormalPadding(FMargin(10.f, 4.f));
		Style.SetPressedPadding(FMargin(10.f, 4.f));
		Button->SetStyle(Style);
		UTextBlock* Label = Text(T, 14, true, SSPalette::Sand100());
		Label->SetText(FText::FromString(Glyph));
		Button->AddChild(Label);
		return Button;
	}
}

void USSSettingRow::Step(int32 Delta)
{
	if (Options.Num() == 0)
	{
		return;
	}
	Index = (Index + Delta + Options.Num()) % Options.Num();
	Refresh();
	if (OnChanged)
	{
		OnChanged(Index);
	}
}

void USSSettingRow::Refresh()
{
	if (ValueText && Options.IsValidIndex(Index))
	{
		ValueText->SetText(Options[Index]);
	}
}

USSSettingRow* USSSettingsWidget::AddRow(UVerticalBox* Box, const FText& Label, TArray<FText> Options, int32 Current, TFunction<void(int32)> OnChanged)
{
	UWidgetTree* T = WidgetTree;
	USSSettingRow* Row = NewObject<USSSettingRow>(this);
	Row->Options = MoveTemp(Options);
	Row->Index = FMath::Clamp(Current, 0, FMath::Max(0, Row->Options.Num() - 1));
	Row->OnChanged = MoveTemp(OnChanged);

	UBorder* Plate1 = Plate(T, SSPalette::Field800(0.85f), FMargin(16.f, 8.f));
	UHorizontalBox* Line = T->ConstructWidget<UHorizontalBox>();
	Plate1->SetContent(Line);
	UTextBlock* Name = Text(T, 13, true, SSPalette::Sage200(), 160);
	Name->SetText(Label.ToUpper());
	AddH(Line, Name, true);

	UButton* Prev = ArrowButton(T, TEXT("‹"));
	FScriptDelegate PrevDelegate;
	PrevDelegate.BindUFunction(Row, GET_FUNCTION_NAME_CHECKED(USSSettingRow, Prev));
	Prev->OnClicked.Add(PrevDelegate);
	AddH(Line, Prev);

	USizeBox* ValueSize = T->ConstructWidget<USizeBox>();
	ValueSize->SetWidthOverride(200.f);
	Row->ValueText = Text(T, 14, true, SSPalette::Sand100(), 60);
	Row->ValueText->SetJustification(ETextJustify::Center);
	ValueSize->AddChild(Row->ValueText);
	AddH(Line, ValueSize);

	UButton* Next = ArrowButton(T, TEXT("›"));
	FScriptDelegate NextDelegate;
	NextDelegate.BindUFunction(Row, GET_FUNCTION_NAME_CHECKED(USSSettingRow, Next));
	Next->OnClicked.Add(NextDelegate);
	AddH(Line, Next);

	AddV(Box, Plate1, 4.f);
	Row->RowWidget = Plate1;
	Row->Refresh();
	Rows.Add(Row);
	Animated.Add(Plate1);
	return Row;
}

bool USSSettingsWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Blurred, darkened backdrop over whatever is behind (menu art or the match).
	UBackgroundBlur* Blur = T->ConstructWidget<UBackgroundBlur>();
	Blur->SetBlurStrength(8.f);
	Fill(Root, Blur);
	Fill(Root, Plate(T, SSPalette::Ink950(0.55f), FMargin(0.f)));

	UVerticalBox* Frame = T->ConstructWidget<UVerticalBox>();
	Panel = Frame;
	Pin(Root, Frame, FVector2D(0.5f, 0.5f), FVector2D(0.f, 0.f));
	AddV(Frame, Rule(T, SSPalette::Brass500(), 2.f, 720.f));
	UBorder* Body = Plate(T, SSPalette::Ink900(0.94f), FMargin(28.f, 20.f, 28.f, 24.f));
	AddV(Frame, Body);
	USizeBox* Width = T->ConstructWidget<USizeBox>();
	Width->SetWidthOverride(664.f);
	Body->SetContent(Width);
	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Width->AddChild(Col);

	UTextBlock* Kicker = Text(T, 11, true, SSPalette::Brass300(), 300);
	Kicker->SetText(NSLOCTEXT("SSSettings", "Kicker", "SOUTHERN SPEAR"));
	AddV(Col, Kicker);
	UTextBlock* Title = Text(T, 32, true, SSPalette::Sand100(), 100);
	Title->SetText(NSLOCTEXT("SSSettings", "Title", "SETTINGS"));
	AddV(Col, Title, 2.f);

	UGameUserSettings* S = Settings();

	// Tabs across the top (website nav style); one scrolling page per tab.
	UHorizontalBox* TabBar = T->ConstructWidget<UHorizontalBox>();
	AddV(Col, TabBar, 16.f);
	AddV(Col, Rule(T, SSPalette::Line(), 1.f, 664.f), 0.f);
	USizeBox* PageSize = T->ConstructWidget<USizeBox>();
	PageSize->SetHeightOverride(430.f);
	AddV(Col, PageSize, 10.f);
	UScrollBox* Scroll = T->ConstructWidget<UScrollBox>();
	PageSize->AddChild(Scroll);
	const FText TabNames[] = {
		NSLOCTEXT("SSSettings", "TabDisplay", "DISPLAY"), NSLOCTEXT("SSSettings", "TabGraphics", "GRAPHICS"),
		NSLOCTEXT("SSSettings", "TabAudio", "AUDIO"), NSLOCTEXT("SSSettings", "TabControls", "CONTROLS"),
		NSLOCTEXT("SSSettings", "TabInterface", "INTERFACE") };
	const FName TabHandlers[] = {
		GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnTab0), GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnTab1),
		GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnTab2), GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnTab3),
		GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnTab4) };
	auto Flat = [](const FLinearColor& C) { FSlateBrush B; B.DrawAs = ESlateBrushDrawType::Box; B.TintColor = FSlateColor(C); return B; };
	for (int32 Tab = 0; Tab < UE_ARRAY_COUNT(TabNames); ++Tab)
	{
		UButton* TabButton = T->ConstructWidget<UButton>();
		FButtonStyle Style = TabButton->GetStyle();
		Style.SetNormal(Flat(FLinearColor::Transparent));
		Style.SetHovered(Flat(SSPalette::Field700(0.8f)));
		Style.SetPressed(Flat(SSPalette::Field700()));
		Style.SetNormalPadding(FMargin(14.f, 8.f));
		Style.SetPressedPadding(FMargin(14.f, 8.f));
		TabButton->SetStyle(Style);
		UVerticalBox* TabBody = T->ConstructWidget<UVerticalBox>();
		UTextBlock* TabLabel = Text(T, 13, true, SSPalette::Sage400(), 180);
		TabLabel->SetText(TabNames[Tab]);
		AddV(TabBody, TabLabel, 0.f, HAlign_Center);
		UBorder* Underline = Plate(T, SSPalette::Brass500(), FMargin(0.f));
		USizeBox* UnderlineSize = T->ConstructWidget<USizeBox>();
		UnderlineSize->SetHeightOverride(2.f);
		UnderlineSize->AddChild(Underline);
		AddV(TabBody, UnderlineSize, 6.f);
		TabButton->AddChild(TabBody);
		FScriptDelegate TabDelegate;
		TabDelegate.BindUFunction(this, TabHandlers[Tab]);
		TabButton->OnClicked.Add(TabDelegate);
		AddH(TabBar, TabButton);
		TabLabels.Add(TabLabel);
		TabUnderlines.Add(Underline);
		UVerticalBox* Page = T->ConstructWidget<UVerticalBox>();
		Scroll->AddChild(Page);
		Pages.Add(Page);
	}
	UVerticalBox* DisplayPage = Pages[0];
	UVerticalBox* GraphicsPage = Pages[1];
	UVerticalBox* AudioPage = Pages[2];
	UVerticalBox* ControlsPage = Pages[3];
	UVerticalBox* InterfacePage = Pages[4];
	const TArray<FText> OffOn = { NSLOCTEXT("SSSettings", "Off", "Off"), NSLOCTEXT("SSSettings", "On", "On") };
	auto IntPref = [](const TCHAR* Key) { return [Key](int32 I) { FSSUserPrefs::SetInt(Key, I); FSSUserPrefs::ApplyRendering(); }; };

	// DISPLAY
	const EWindowMode::Type Mode = S ? S->GetFullscreenMode() : EWindowMode::Windowed;
	int32 ModeIndex = 2;
	for (int32 I = 0; I < 3; ++I) { if (WindowModes[I] == Mode) { ModeIndex = I; } }
	AddRow(DisplayPage, NSLOCTEXT("SSSettings", "WindowMode", "Window mode"),
		{ NSLOCTEXT("SSSettings", "Fullscreen", "Fullscreen"), NSLOCTEXT("SSSettings", "Borderless", "Borderless"), NSLOCTEXT("SSSettings", "Windowed", "Windowed") },
		ModeIndex, [](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetFullscreenMode(WindowModes[I]); } });

	UKismetSystemLibrary::GetSupportedFullscreenResolutions(Resolutions);
	if (Resolutions.Num() == 0)
	{
		Resolutions = { FIntPoint(1280, 720), FIntPoint(1600, 900), FIntPoint(1920, 1080), FIntPoint(2560, 1440) };
	}
	TArray<FText> ResText;
	int32 ResIndex = Resolutions.Num() - 1;
	const FIntPoint Current = S ? S->GetScreenResolution() : FIntPoint(1920, 1080);
	for (int32 I = 0; I < Resolutions.Num(); ++I)
	{
		ResText.Add(FText::FromString(FString::Printf(TEXT("%d × %d"), Resolutions[I].X, Resolutions[I].Y)));
		if (Resolutions[I] == Current) { ResIndex = I; }
	}
	TArray<FIntPoint> ResCopy = Resolutions;
	AddRow(DisplayPage, NSLOCTEXT("SSSettings", "Resolution", "Resolution"), ResText, ResIndex,
		[ResCopy](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetScreenResolution(ResCopy[I]); } });

	AddRow(DisplayPage, NSLOCTEXT("SSSettings", "VSync", "Vertical sync"), OffOn,
		S && S->IsVSyncEnabled() ? 1 : 0, [](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetVSyncEnabled(I == 1); } });

	int32 LimitIndex = UE_ARRAY_COUNT(FrameLimits) - 1;
	const float Limit = S ? S->GetFrameRateLimit() : 0.f;
	TArray<FText> LimitText;
	for (int32 I = 0; I < UE_ARRAY_COUNT(FrameLimits); ++I)
	{
		LimitText.Add(FrameLimits[I] ? FText::AsNumber(FrameLimits[I]) : NSLOCTEXT("SSSettings", "Unlimited", "Unlimited"));
		if (FMath::IsNearlyEqual(Limit, static_cast<float>(FrameLimits[I]))) { LimitIndex = I; }
	}
	AddRow(DisplayPage, NSLOCTEXT("SSSettings", "FrameLimit", "Frame rate limit"), LimitText, LimitIndex,
		[](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetFrameRateLimit(static_cast<float>(FrameLimits[I])); } });

	TArray<FText> FovText;
	int32 FovIndex = 0;
	const int32 FovNow = FMath::RoundToInt(FSSUserPrefs::GetFieldOfView());
	for (int32 Fov = static_cast<int32>(FSSUserPrefs::MinFieldOfView), I = 0; Fov <= static_cast<int32>(FSSUserPrefs::MaxFieldOfView); Fov += 5, ++I)
	{
		FovText.Add(FText::FromString(FString::Printf(TEXT("%d°"), Fov)));
		if (Fov <= FovNow) { FovIndex = I; }
	}
	AddRow(DisplayPage, NSLOCTEXT("SSSettings", "Fov", "Field of view"), FovText, FovIndex,
		[](int32 I) { FSSUserPrefs::SetFieldOfView(FSSUserPrefs::MinFieldOfView + 5.f * I); });

	TArray<FText> BrightText;
	for (int32 Step = -4; Step <= 4; ++Step) { BrightText.Add(FText::FromString(Step > 0 ? FString::Printf(TEXT("+%d"), Step) : FString::FromInt(Step))); }
	const int32 BrightIndex = FMath::Clamp(FMath::RoundToInt((FSSUserPrefs::GetFloat(FSSUserPrefs::Brightness(), 2.2f) - 1.8f) / 0.1f), 0, 8);
	AddRow(DisplayPage, NSLOCTEXT("SSSettings", "Brightness", "Brightness"), BrightText, BrightIndex,
		[](int32 I) { FSSUserPrefs::SetFloat(FSSUserPrefs::Brightness(), 1.8f + 0.1f * I); FSSUserPrefs::ApplyRendering(); });

	// GRAPHICS
	const TArray<FText> Levels = { NSLOCTEXT("SSSettings", "Low", "Low"), NSLOCTEXT("SSSettings", "Medium", "Medium"),
		NSLOCTEXT("SSSettings", "High", "High"), NSLOCTEXT("SSSettings", "Epic", "Epic"), NSLOCTEXT("SSSettings", "Cinematic", "Cinematic") };
	TArray<FText> PresetText = Levels;
	PresetText.Add(NSLOCTEXT("SSSettings", "Custom", "Custom"));
	const int32 Overall = S ? S->GetOverallScalabilityLevel() : 3;
	PresetRow = AddRow(GraphicsPage, NSLOCTEXT("SSSettings", "Quality", "Quality preset"), PresetText,
		Overall < 0 ? 5 : FMath::Clamp(Overall, 0, 4), [this](int32 I)
		{
			UGameUserSettings* G = Settings();
			if (!G || I > 4) { return; }
			G->SetOverallScalabilityLevel(I);
			for (USSSettingRow* Row : QualityRows) { Row->Index = I; Row->Refresh(); }
		});
	struct FQuality { FText Name; int32 (UGameUserSettings::*Get)() const; void (UGameUserSettings::*Set)(int32); };
	const FQuality Qualities[] = {
		{ NSLOCTEXT("SSSettings", "ViewDistance", "View distance"), &UGameUserSettings::GetViewDistanceQuality, &UGameUserSettings::SetViewDistanceQuality },
		{ NSLOCTEXT("SSSettings", "Shadows", "Shadows"), &UGameUserSettings::GetShadowQuality, &UGameUserSettings::SetShadowQuality },
		{ NSLOCTEXT("SSSettings", "GI", "Global illumination"), &UGameUserSettings::GetGlobalIlluminationQuality, &UGameUserSettings::SetGlobalIlluminationQuality },
		{ NSLOCTEXT("SSSettings", "Reflections", "Reflections"), &UGameUserSettings::GetReflectionQuality, &UGameUserSettings::SetReflectionQuality },
		{ NSLOCTEXT("SSSettings", "Textures", "Textures"), &UGameUserSettings::GetTextureQuality, &UGameUserSettings::SetTextureQuality },
		{ NSLOCTEXT("SSSettings", "Effects", "Effects"), &UGameUserSettings::GetVisualEffectQuality, &UGameUserSettings::SetVisualEffectQuality },
		{ NSLOCTEXT("SSSettings", "Foliage", "Foliage"), &UGameUserSettings::GetFoliageQuality, &UGameUserSettings::SetFoliageQuality },
		{ NSLOCTEXT("SSSettings", "PostProcess", "Post-processing"), &UGameUserSettings::GetPostProcessingQuality, &UGameUserSettings::SetPostProcessingQuality },
		{ NSLOCTEXT("SSSettings", "Shading", "Shading"), &UGameUserSettings::GetShadingQuality, &UGameUserSettings::SetShadingQuality },
		{ NSLOCTEXT("SSSettings", "AAQuality", "Anti-aliasing quality"), &UGameUserSettings::GetAntiAliasingQuality, &UGameUserSettings::SetAntiAliasingQuality },
	};
	for (const FQuality& Q : Qualities)
	{
		const auto Set = Q.Set;
		QualityRows.Add(AddRow(GraphicsPage, Q.Name, Levels, S ? FMath::Clamp((S->*Q.Get)(), 0, 4) : 3, [this, Set](int32 I)
		{
			if (UGameUserSettings* G = Settings()) { (G->*Set)(I); }
			if (PresetRow) { PresetRow->Index = 5; PresetRow->Refresh(); } // Custom
		}));
	}
	TArray<FText> ScaleText;
	for (int32 Pct = 50; Pct <= 100; Pct += 5) { ScaleText.Add(FText::FromString(FString::Printf(TEXT("%d%%"), Pct))); }
	const int32 ScaleIndex = S ? FMath::Clamp(FMath::RoundToInt((S->GetResolutionScaleNormalized() * 100.f - 50.f) / 5.f), 0, 10) : 10;
	AddRow(GraphicsPage, NSLOCTEXT("SSSettings", "ResScale", "Render resolution"), ScaleText, ScaleIndex,
		[](int32 I) { if (UGameUserSettings* G = Settings()) { G->SetResolutionScaleNormalized((50.f + 5.f * I) / 100.f); } });
	AddRow(GraphicsPage, NSLOCTEXT("SSSettings", "AAMethod", "Anti-aliasing"),
		{ FText::FromString(TEXT("TSR")), FText::FromString(TEXT("TAA")), FText::FromString(TEXT("FXAA")), NSLOCTEXT("SSSettings", "Off", "Off") },
		FSSUserPrefs::GetInt(FSSUserPrefs::AntiAliasing(), 0), IntPref(FSSUserPrefs::AntiAliasing()));
	AddRow(GraphicsPage, NSLOCTEXT("SSSettings", "RayTracing", "Hardware ray tracing"), OffOn,
		FSSUserPrefs::GetInt(FSSUserPrefs::RayTracing(), 1), IntPref(FSSUserPrefs::RayTracing()));
	AddRow(GraphicsPage, NSLOCTEXT("SSSettings", "RTShadows", "Ray-traced shadows"), OffOn,
		FSSUserPrefs::GetInt(FSSUserPrefs::RayTracedShadows(), 0), IntPref(FSSUserPrefs::RayTracedShadows()));
	AddRow(GraphicsPage, NSLOCTEXT("SSSettings", "MotionBlur", "Motion blur"), OffOn,
		FSSUserPrefs::GetInt(FSSUserPrefs::MotionBlur(), 1), IntPref(FSSUserPrefs::MotionBlur()));

	// AUDIO (the Lyra bridge applies these to Lyra's sound mixes)
	TArray<FText> Percent;
	for (int32 Pct = 0; Pct <= 100; Pct += 10) { Percent.Add(FText::FromString(FString::Printf(TEXT("%d%%"), Pct))); }
	auto Volume = [this, &Percent, AudioPage](const FText& Name, const TCHAR* Key)
	{
		AddRow(AudioPage, Name, Percent, FMath::RoundToInt(FSSUserPrefs::GetFloat(Key, 1.f) * 10.f),
			[Key](int32 I) { FSSUserPrefs::SetFloat(Key, I / 10.f); });
	};
	Volume(NSLOCTEXT("SSSettings", "Master", "Master volume"), FSSUserPrefs::MasterVolume());
	Volume(NSLOCTEXT("SSSettings", "EffectsVolume", "Effects volume"), FSSUserPrefs::EffectsVolume());
	Volume(NSLOCTEXT("SSSettings", "Music", "Music volume"), FSSUserPrefs::MusicVolume());

	// CONTROLS (the Lyra bridge applies these to Lyra's input settings)
	TArray<FText> SensText;
	for (int32 Step = 2; Step <= 30; ++Step) { SensText.Add(FText::FromString(FString::Printf(TEXT("%.1f"), Step / 10.f))); }
	AddRow(ControlsPage, NSLOCTEXT("SSSettings", "Sensitivity", "Mouse sensitivity"), SensText,
		FMath::Clamp(FMath::RoundToInt(FSSUserPrefs::GetFloat(FSSUserPrefs::Sensitivity(), 1.f) * 10.f) - 2, 0, 28),
		[](int32 I) { FSSUserPrefs::SetFloat(FSSUserPrefs::Sensitivity(), (I + 2) / 10.f); });
	AddRow(ControlsPage, NSLOCTEXT("SSSettings", "InvertY", "Invert look"), OffOn,
		FSSUserPrefs::GetInt(FSSUserPrefs::InvertY(), 0), [](int32 I) { FSSUserPrefs::SetInt(FSSUserPrefs::InvertY(), I); });

	// INTERFACE
	AddRow(InterfacePage, NSLOCTEXT("SSSettings", "ShowFps", "Frame rate counter"), OffOn,
		FSSUserPrefs::GetInt(FSSUserPrefs::ShowFps(), 0), [](int32 I) { FSSUserPrefs::SetInt(FSSUserPrefs::ShowFps(), I); });
	AddRow(InterfacePage, NSLOCTEXT("SSSettings", "DevMessages", "Developer messages"), OffOn,
		FSSUserPrefs::GetInt(FSSUserPrefs::DevMessages(), 0), IntPref(FSSUserPrefs::DevMessages()));

	SelectTab(0);

	// Buttons.
	UHorizontalBox* Buttons = T->ConstructWidget<UHorizontalBox>();
	AddV(Col, Buttons, 22.f, HAlign_Right);
	UButton* Back = MenuButton(T, NSLOCTEXT("SSSettings", "Back", "BACK"), 150.f);
	FScriptDelegate BackDelegate;
	BackDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnBack));
	Back->OnClicked.Add(BackDelegate);
	AddH(Buttons, Back)->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
	UButton* Apply = MenuButton(T, NSLOCTEXT("SSSettings", "Apply", "APPLY"), 150.f, /*bPrimary=*/ true);
	FScriptDelegate ApplyDelegate;
	ApplyDelegate.BindUFunction(this, GET_FUNCTION_NAME_CHECKED(USSSettingsWidget, OnApply));
	Apply->OnClicked.Add(ApplyDelegate);
	AddH(Buttons, Apply);
	Animated.Add(Buttons);
	return true;
}

void USSSettingsWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	Reveal(Panel, Ease(Elapsed, 0.f, 0.3f), 18.f, /*bVertical=*/ true);
	for (int32 Index = 0; Index < Animated.Num(); ++Index)
	{
		Reveal(Animated[Index], Ease(Elapsed, 0.08f + 0.04f * Index, 0.3f), 16.f);
	}
}

void USSSettingsWidget::OnApply()
{
	if (UGameUserSettings* S = Settings())
	{
		S->ApplySettings(/*bCheckForCommandLineOverrides=*/ false);
		S->SaveSettings();
	}
	OnBack();
}

void USSSettingsWidget::SelectTab(int32 Tab)
{
	for (int32 Index = 0; Index < Pages.Num(); ++Index)
	{
		const bool bOn = Index == Tab;
		Pages[Index]->SetVisibility(bOn ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
		TabLabels[Index]->SetColorAndOpacity(bOn ? SSPalette::Sand100() : SSPalette::Sage400());
		TabUnderlines[Index]->SetRenderOpacity(bOn ? 1.f : 0.f);
	}
	Elapsed = FMath::Min(Elapsed, 0.08f); // replay the row reveal for the new page
}

void USSSettingsWidget::OnBack()
{
	SetVisibility(ESlateVisibility::Collapsed);
	if (OnClosed)
	{
		OnClosed();
	}
}
