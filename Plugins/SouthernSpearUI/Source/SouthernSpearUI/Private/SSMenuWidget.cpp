// Copyright Southern Spear. All Rights Reserved.

#include "SSMenuWidget.h"

#include "Components/BackgroundBlur.h"
#include "Components/ScaleBox.h"
#include "Components/UniformGridPanel.h"
#include "HAL/PlatformProcess.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameInstance.h"
#include "Kismet/KismetSystemLibrary.h"
#include "SSLocalHudState.h"
#include "SSLocalProfileState.h"
#include "SSSettingsWidget.h"
#include "SSUIAssets.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

const TCHAR* USSMenuWidget::FrontEndMap = TEXT("/Game/Maps/L_SS_FrontEnd");
int32 USSMenuWidget::SelectedBots = 8;
bool USSMenuWidget::bSelectedSectionRules = false;

namespace
{
	constexpr float PanelWidth = 470.f;

	FSlateBrush Flat(const FLinearColor& C)
	{
		FSlateBrush Brush;
		Brush.DrawAs = ESlateBrushDrawType::Box;
		Brush.TintColor = FSlateColor(C);
		return Brush;
	}

	void StyleButton(UButton* Button, const FLinearColor& Normal, const FLinearColor& Hover, const FMargin& Padding)
	{
		FButtonStyle Style = Button->GetStyle();
		Style.SetNormal(Flat(Normal));
		Style.SetHovered(Flat(Hover));
		Style.SetPressed(Flat(SSPalette::Brass300()));
		Style.SetNormalPadding(Padding);
		Style.SetPressedPadding(Padding);
		Button->SetStyle(Style);
	}

	UWidget* KeyArt(UWidgetTree* T)
	{
		UImage* Art = T->ConstructWidget<UImage>();
		if (UTexture2D* Texture = SSUIAssets::MainMenuArt())
		{
			Art->SetBrushFromTexture(Texture, /*bMatchSize=*/ true);
		}
		UScaleBox* Scale = T->ConstructWidget<UScaleBox>();
		Scale->SetStretch(EStretch::ScaleToFill);
		Scale->AddChild(Art);
		return Scale;
	}

	/** Operation card, as the website cards: hairline frame, brass kicker, title, copy, deploy cue. */
	UButton* MapCard(UWidgetTree* T, const FText& Title, const FText& Description, const FText& Meta)
	{
		UButton* Button = T->ConstructWidget<UButton>();
		StyleButton(Button, SSPalette::Brass500(0.28f), SSPalette::Brass500(0.9f), FMargin(1.f));
		UBorder* Inner = Plate(T, SSPalette::Ink900(0.9f), FMargin(18.f, 14.f, 18.f, 14.f));
		Button->AddChild(Inner);
		USizeBox* Size = T->ConstructWidget<USizeBox>();
		Size->SetWidthOverride(300.f);
		Size->SetHeightOverride(144.f);
		Inner->SetContent(Size);
		UVerticalBox* Body = T->ConstructWidget<UVerticalBox>();
		Size->AddChild(Body);
		UTextBlock* MetaText = Text(T, 10, true, SSPalette::Brass500(), 220);
		MetaText->SetText(Meta);
		AddV(Body, MetaText);
		UTextBlock* TitleText = Text(T, 21, true, SSPalette::Sand100(), 20);
		TitleText->SetText(Title);
		AddV(Body, TitleText, 4.f);
		UTextBlock* DescText = Text(T, 12, false, SSPalette::Sage200());
		DescText->SetText(Description);
		DescText->SetAutoWrapText(true);
		AddV(Body, DescText, 4.f);
		AddV(Body, T->ConstructWidget<USpacer>())->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		UTextBlock* Go = Text(T, 11, true, SSPalette::Brass300(), 240);
		Go->SetText(NSLOCTEXT("SSMenu", "DeployCue", "DEPLOY  ›"));
		AddV(Body, Go);
		return Button;
	}

	/** Website primary button: brass fill, ink label. */
	UButton* PrimaryButton(UWidgetTree* T, const FText& Label, float Width)
	{
		UButton* Button = T->ConstructWidget<UButton>();
		StyleButton(Button, SSPalette::Brass500(), SSPalette::Brass300(), FMargin(18.f, 9.f));
		UTextBlock* LabelText = Text(T, 13, true, SSPalette::Ink950(), 200);
		LabelText->SetText(Label);
		LabelText->SetShadowColorAndOpacity(FLinearColor::Transparent);
		LabelText->SetJustification(ETextJustify::Center);
		if (Width > 0.f)
		{
			USizeBox* Size = T->ConstructWidget<USizeBox>();
			Size->SetWidthOverride(Width);
			Size->AddChild(LabelText);
			Button->AddChild(Size);
		}
		else
		{
			Button->AddChild(LabelText);
		}
		return Button;
	}

	/** Website secondary / nav button: transparent with a faint hover. */
	UButton* GhostButton(UWidgetTree* T, const FText& Label, bool bFramed)
	{
		UButton* Button = T->ConstructWidget<UButton>();
		StyleButton(Button, bFramed ? SSPalette::Ink950(0.5f) : FLinearColor::Transparent, SSPalette::Field700(0.9f), FMargin(14.f, 9.f));
		UTextBlock* LabelText = Text(T, 13, true, SSPalette::Sand100(), 200);
		LabelText->SetText(Label);
		Button->AddChild(LabelText);
		return Button;
	}

	/** Small caption with a short brass rule, as on the website section heads. */
	UWidget* Caption(UWidgetTree* T, const FText& Label)
	{
		UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
		AddH(Row, Rule(T, SSPalette::Brass500(), 2.f, 22.f));
		UTextBlock* CaptionText = Text(T, 11, true, SSPalette::Brass300(), 300);
		CaptionText->SetText(Label);
		AddH(Row, CaptionText)->SetPadding(FMargin(10.f, 0.f, 0.f, 0.f));
		return Row;
	}
}

UButton* USSMenuWidget::AddHandler(UButton* Button, FName Handler)
{
	FScriptDelegate Delegate;
	Delegate.BindUFunction(this, Handler);
	Button->OnClicked.Add(Delegate);
	return Button;
}

void USSMenuWidget::Setup(ESSMenuMode InMode)
{
	Mode = InMode;
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;
	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Content = Col;

	if (Mode == ESSMenuMode::FrontEnd)
	{
		// Website hero: full-bleed key art, darkened towards the left and the bottom.
		Fill(Root, KeyArt(T));
		// Sixteen thin steps read as a smooth left-to-right gradient.
		for (int32 Index = 0; Index < 16; ++Index)
		{
			UCanvasPanelSlot* ShadeSlot = Root->AddChildToCanvas(Plate(T, SSPalette::Ink950(0.055f), FMargin(0.f)));
			ShadeSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 1.f));
			ShadeSlot->SetOffsets(FMargin(0.f, 0.f, 1150.f - 40.f * Index, 0.f));
		}
		UCanvasPanelSlot* FloorSlot = Root->AddChildToCanvas(Plate(T, SSPalette::Ink950(0.55f), FMargin(0.f)));
		FloorSlot->SetAnchors(FAnchors(0.f, 1.f, 1.f, 1.f));
		FloorSlot->SetAlignment(FVector2D(0.f, 1.f));
		FloorSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 64.f));

		// Top bar, as the website header: badge and stacked wordmark left, nav right.
		UBorder* TopBar = Plate(T, SSPalette::Ink950(0.78f), FMargin(64.f, 12.f));
		UCanvasPanelSlot* TopSlot = Root->AddChildToCanvas(TopBar);
		TopSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		TopSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 68.f));
		UHorizontalBox* TopRow = T->ConstructWidget<UHorizontalBox>();
		TopBar->SetContent(TopRow);
		if (UTexture2D* Logo = SSUIAssets::Logo())
		{
			UImage* Badge = T->ConstructWidget<UImage>();
			Badge->SetBrushFromTexture(Logo);
			Badge->SetDesiredSizeOverride(FVector2D(40.f, 40.f));
			AddH(TopRow, Badge)->SetPadding(FMargin(0.f, 0.f, 12.f, 0.f));
		}
		UVerticalBox* Wordmark = T->ConstructWidget<UVerticalBox>();
		UTextBlock* Mark = Text(T, 15, true, SSPalette::Sand100(), 220);
		Mark->SetText(NSLOCTEXT("SSMenu", "Mark", "SOUTHERN SPEAR"));
		AddV(Wordmark, Mark);
		UTextBlock* Phase = Text(T, 10, true, SSPalette::Brass500(), 260);
		Phase->SetText(NSLOCTEXT("SSMenu", "Phase", "PRE-ALPHA"));
		AddV(Wordmark, Phase);
		AddH(TopRow, Wordmark);
		AddH(TopRow, T->ConstructWidget<USpacer>(), true);

		// Service profile (ADR-032): callsign, rank and service XP from the local record.
		const UGameInstance* GameInstance = GetGameInstance();
		const USSLocalProfileState* Profile = GameInstance ? GameInstance->GetSubsystem<USSLocalProfileState>() : nullptr;
		if (Profile && Profile->bLoaded)
		{
			UVerticalBox* ProfileBox = T->ConstructWidget<UVerticalBox>();
			UTextBlock* Who = Text(T, 13, true, SSPalette::Sand100(), 160);
			Who->SetText(FText::Format(NSLOCTEXT("SSMenu", "ProfileWho", "{0}  ·  {1}"),
				Profile->RankAbbreviation, FText::FromString(Profile->Callsign.ToUpper())));
			Who->SetJustification(ETextJustify::Right);
			AddV(ProfileBox, Who);
			UTextBlock* Xp = Text(T, 10, true, SSPalette::Brass500(), 200);
			Xp->SetText(Profile->NextRankXp < 0
				? FText::Format(NSLOCTEXT("SSMenu", "ProfileXpTop", "{0}  ·  {1} XP"), Profile->RankName, FText::AsNumber(Profile->ServiceXp))
				: FText::Format(NSLOCTEXT("SSMenu", "ProfileXp", "{0}  ·  {1} / {2} XP"), Profile->RankName,
					FText::AsNumber(Profile->ServiceXp), FText::AsNumber(Profile->NextRankXp)));
			Xp->SetJustification(ETextJustify::Right);
			AddV(ProfileBox, Xp);
			AddH(TopRow, ProfileBox)->SetPadding(FMargin(0.f, 0.f, 24.f, 0.f));
		}
		const TPair<FText, FName> Nav[] = {
			{ NSLOCTEXT("SSMenu", "NavSettings", "SETTINGS"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSettings) },
			{ NSLOCTEXT("SSMenu", "NavQuit", "QUIT"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnQuit) } };
		for (const TPair<FText, FName>& Item : Nav)
		{
			AddH(TopRow, AddHandler(GhostButton(T, Item.Key, false), Item.Value))->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
		}
		AddH(TopRow, AddHandler(PrimaryButton(T, NSLOCTEXT("SSMenu", "Discord", "DISCORD"), 0.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnDiscord)))->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f));
		UCanvasPanelSlot* TopRuleSlot = Root->AddChildToCanvas(Rule(T, SSPalette::Brass500(0.28f), 1.f));
		TopRuleSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		TopRuleSlot->SetOffsets(FMargin(0.f, 68.f, 0.f, 1.f));

		// Hero copy, left, then the operations grid.
		Pin(Root, Col, FVector2D(0.f, 0.5f), FVector2D(64.f, 30.f));
		UBorder* Chip = Plate(T, SSPalette::Ink950(0.6f), FMargin(10.f, 5.f));
		UHorizontalBox* ChipRow = T->ConstructWidget<UHorizontalBox>();
		Chip->SetContent(ChipRow);
		UTextBlock* Dot = Text(T, 10, true, SSPalette::Brass500());
		Dot->SetText(FText::FromString(TEXT("●")));
		AddH(ChipRow, Dot)->SetPadding(FMargin(0.f, 0.f, 8.f, 0.f));
		UTextBlock* ChipText = Text(T, 10, true, SSPalette::Sand100(), 240);
		ChipText->SetText(NSLOCTEXT("SSMenu", "Chip", "PRE-ALPHA  ·  OFFLINE WITH BOTS"));
		AddH(ChipRow, ChipText);
		AddV(Col, Stagger(Chip), 0.f, HAlign_Left);
		TitleText = Text(T, 44, true, SSPalette::Sand100(), 20);
		TitleText->SetText(NSLOCTEXT("SSMenu", "Headline", "An Australian-inspired tactical\nmultiplayer experience."));
		AddV(Col, Stagger(TitleText), 14.f);
		UTextBlock* Lede = Text(T, 15, false, SSPalette::Sage200());
		Lede->SetText(NSLOCTEXT("SSMenu", "Lede", "Teamwork, communication and objective-focused infantry combat.\nChoose an operation and deploy with 3rd Battalion."));
		AddV(Col, Stagger(Lede), 10.f);

		AddV(Col, Stagger(Caption(T, NSLOCTEXT("SSMenu", "Operations", "OPERATIONS"))), 26.f);
		UUniformGridPanel* Grid = T->ConstructWidget<UUniformGridPanel>();
		Grid->SetSlotPadding(FMargin(4.f));
		AddV(Col, Stagger(Grid), 8.f, HAlign_Left);
		struct FOp { FText Title, Description, Meta; FName Handler; };
		const FOp Ops[] = {
			{ NSLOCTEXT("SSMenu", "RedGum", "Red Gum Station"),
			  NSLOCTEXT("SSMenu", "RedGumDesc", "An outback cattle station: the north paddock, the homestead, the south paddock."),
			  NSLOCTEXT("SSMenu", "RedGumMeta", "3 OBJECTIVES  ·  OPEN PADDOCKS"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnRedGum) },
			{ NSLOCTEXT("SSMenu", "DryRiver", "Dry River"),
			  NSLOCTEXT("SSMenu", "DryRiverDesc", "A dry creek line between a water point and a farmstead."),
			  NSLOCTEXT("SSMenu", "DryRiverMeta", "2 OBJECTIVES  ·  CREEK BED"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnDryRiver) },
			{ NSLOCTEXT("SSMenu", "Saltbush", "Saltbush Flats"),
			  NSLOCTEXT("SSMenu", "SaltbushDesc", "Arid scrub and stone country: a windmill, the stock yards, a dry dam."),
			  NSLOCTEXT("SSMenu", "SaltbushMeta", "3 OBJECTIVES  ·  ROCKY COVER"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSaltbush) },
			{ NSLOCTEXT("SSMenu", "SelatCanal", "Selat Canal"),
			  NSLOCTEXT("SSMenu", "SelatCanalDesc", "A Murasian canal district: the footbridge, market row, the pump house."),
			  NSLOCTEXT("SSMenu", "SelatCanalMeta", "SPECIAL FORCES  ·  CLOSE QUARTERS"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSelatCanal) },
			{ NSLOCTEXT("SSMenu", "Bluestone", "Bluestone Quarry"),
			  NSLOCTEXT("SSMenu", "BluestoneDesc", "A flooded slate pit: the loading bay, the cutting face, the spoil heaps."),
			  NSLOCTEXT("SSMenu", "BluestoneMeta", "3 OBJECTIVES  ·  CLOSE QUARTERS"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBluestone) },
		};
		for (int32 Index = 0; Index < UE_ARRAY_COUNT(Ops); ++Index)
		{
			Grid->AddChildToUniformGrid(AddHandler(MapCard(T, Ops[Index].Title, Ops[Index].Description, Ops[Index].Meta), Ops[Index].Handler),
				Index / 2, Index % 2);
		}

		// Bots: 4 / 8 / 12.
		AddV(Col, Stagger(Caption(T, NSLOCTEXT("SSMenu", "Bots", "BOTS PER MATCH"))), 22.f);
		UHorizontalBox* BotRow = T->ConstructWidget<UHorizontalBox>();
		AddV(Col, Stagger(BotRow), 10.f, HAlign_Left);
		const TPair<int32, FName> Choices[] = {
			{ 4, GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBots4) },
			{ 8, GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBots8) },
			{ 12, GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBots12) } };
		for (const TPair<int32, FName>& Choice : Choices)
		{
			UButton* Button = T->ConstructWidget<UButton>();
			USizeBox* Size = T->ConstructWidget<USizeBox>();
			Size->SetWidthOverride(56.f);
			UTextBlock* Label = Text(T, 15, true, SSPalette::Sand100());
			Label->SetText(FText::AsNumber(Choice.Key));
			Label->SetJustification(ETextJustify::Center);
			Size->AddChild(Label);
			Button->AddChild(Size);
			AddH(BotRow, AddHandler(Button, Choice.Value))->SetPadding(FMargin(0.f, 0.f, 6.f, 0.f));
			BotButtons.Add(Button);
		}
		SetBots(SelectedBots);

		// Rules: the same maps, two rule sets (ADR-018, ADR-031).
		AddV(Col, Stagger(Caption(T, NSLOCTEXT("SSMenu", "Rules", "RULES"))), 22.f);
		UHorizontalBox* RulesRow = T->ConstructWidget<UHorizontalBox>();
		AddV(Col, Stagger(RulesRow), 10.f, HAlign_Left);
		const TPair<FText, FName> RuleChoices[] = {
			{ NSLOCTEXT("SSMenu", "RulesObjective", "OBJECTIVE ASSAULT  ·  RESPAWNS"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnRulesObjective) },
			{ NSLOCTEXT("SSMenu", "RulesSection", "SECTION ASSAULT  ·  ONE LIFE"), GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnRulesSection) } };
		for (const TPair<FText, FName>& Choice : RuleChoices)
		{
			UButton* Button = T->ConstructWidget<UButton>();
			UTextBlock* Label = Text(T, 12, true, SSPalette::Sand100(), 120);
			Label->SetText(Choice.Key);
			Label->SetJustification(ETextJustify::Center);
			Button->AddChild(Label);
			AddH(RulesRow, AddHandler(Button, Choice.Value))->SetPadding(FMargin(0.f, 0.f, 6.f, 0.f));
			RulesButtons.Add(Button);
		}
		SetSectionRules(bSelectedSectionRules);

		UTextBlock* Footer = Text(T, 11, false, SSPalette::Sage400(), 40);
		Footer->SetText(NSLOCTEXT("SSMenu", "Footer", "A fictional setting. Not affiliated with any real defence force."));
		Pin(Root, Stagger(Footer), FVector2D(0.f, 1.f), FVector2D(64.f, -24.f));
		UTextBlock* Keys = Text(T, 11, true, SSPalette::Sage400(), 200);
		Keys->SetText(NSLOCTEXT("SSMenu", "Keys", "WASD MOVE  ·  RMB AIM  ·  R RELOAD  ·  L CLASS  ·  M MAP  ·  ESC MENU"));
		Pin(Root, Stagger(Keys), FVector2D(1.f, 1.f), FVector2D(-64.f, -24.f));

		// Intro: the whole screen rises out of black.
		Curtain = Plate(T, SSPalette::Ink950(), FMargin(0.f));
		Curtain->SetVisibility(ESlateVisibility::HitTestInvisible);
		Fill(Root, Curtain);
	}
	else
	{
		UBackgroundBlur* Blur = T->ConstructWidget<UBackgroundBlur>();
		Blur->SetBlurStrength(6.f);
		Fill(Root, Blur);
		Fill(Root, Plate(T, SSPalette::Ink950(0.45f), FMargin(0.f)));

		// Side panel, full height, sliding in from the left.
		UBorder* Side = Plate(T, SSPalette::Ink900(0.94f), FMargin(56.f, 0.f, 40.f, 0.f));
		SidePanel = Side;
		UCanvasPanelSlot* SideSlot = Root->AddChildToCanvas(Side);
		SideSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 1.f));
		SideSlot->SetOffsets(FMargin(0.f, 0.f, PanelWidth, 0.f));
		Side->SetVerticalAlignment(VAlign_Center);
		Side->SetContent(Col);

		UTextBlock* Kicker = Text(T, 11, true, SSPalette::Brass300(), 300);
		Kicker->SetText(NSLOCTEXT("SSMenu", "Paused", "THE MATCH CONTINUES"));
		AddV(Col, Stagger(Kicker));
		UTextBlock* Title = Text(T, 38, true, SSPalette::Sand100(), 100);
		Title->SetText(NSLOCTEXT("SSMenu", "MatchMenu", "MATCH MENU"));
		AddV(Col, Stagger(Title), 2.f);
		AddV(Col, Stagger(Rule(T, SSPalette::Brass500(), 2.f, 96.f)), 10.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Resume", "RESUME"), 360.f, /*bPrimary=*/ true),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnResume))), 28.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Redeploy", "RE-DEPLOY"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnRedeploy))), 8.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Settings", "SETTINGS"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSettings))), 8.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "MainMenu", "LEAVE MATCH"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnMainMenu))), 8.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "QuitGame", "QUIT TO DESKTOP"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnQuit))), 8.f, HAlign_Left);

		// Controls card, bottom right.
		UVerticalBox* Card = T->ConstructWidget<UVerticalBox>();
		Pin(Root, Stagger(Card), FVector2D(1.f, 1.f), FVector2D(-48.f, -48.f));
		AddV(Card, Rule(T, SSPalette::Brass500(), 2.f, 300.f));
		UBorder* CardPlate = Plate(T, SSPalette::Ink900(0.9f), FMargin(18.f, 12.f, 18.f, 14.f));
		AddV(Card, CardPlate);
		UVerticalBox* CardBody = T->ConstructWidget<UVerticalBox>();
		CardPlate->SetContent(CardBody);
		AddV(CardBody, Caption(T, NSLOCTEXT("SSMenu", "Controls", "CONTROLS")));
		const TPair<const TCHAR*, FText> Bindings[] = {
			{ TEXT("WASD"), NSLOCTEXT("SSMenu", "Move", "Move") },
			{ TEXT("LMB"), NSLOCTEXT("SSMenu", "Fire", "Fire") },
			{ TEXT("RMB"), NSLOCTEXT("SSMenu", "Aim", "Aim down sights") },
			{ TEXT("R"), NSLOCTEXT("SSMenu", "ReloadKey", "Reload") },
			{ TEXT("M"), NSLOCTEXT("SSMenu", "MapKey", "Full map") },
			{ TEXT("ESC"), NSLOCTEXT("SSMenu", "MenuKey", "This menu") } };
		for (const TPair<const TCHAR*, FText>& Binding : Bindings)
		{
			UHorizontalBox* Line = T->ConstructWidget<UHorizontalBox>();
			AddV(CardBody, Line, 6.f);
			USizeBox* KeySize = T->ConstructWidget<USizeBox>();
			KeySize->SetWidthOverride(64.f);
			UTextBlock* Key = Text(T, 12, true, SSPalette::Sand100(), 120);
			Key->SetText(FText::FromString(Binding.Key));
			KeySize->AddChild(Key);
			AddH(Line, KeySize);
			UTextBlock* Action = Text(T, 12, false, SSPalette::Sage200());
			Action->SetText(Binding.Value);
			AddH(Line, Action);
		}
	}
}

void USSMenuWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	// Dev capture: -SSOpenSettings[=<tab>] opens Settings once the intro has played.
	int32 SettingsTab = 0;
	if (!bDevSettingsOpened && Mode == ESSMenuMode::FrontEnd && Elapsed > 2.5f && (FParse::Param(FCommandLine::Get(), TEXT("SSOpenSettings")) || FParse::Value(FCommandLine::Get(), TEXT("SSOpenSettings="), SettingsTab)))
	{
		bDevSettingsOpened = true;
		OnSettings();
		if (Settings) { Settings->SelectTab(SettingsTab); }
	}

	if (Curtain)
	{
		const float Fade = Ease(Elapsed, 0.15f, 0.9f);
		Curtain->SetRenderOpacity(1.f - Fade);
		Curtain->SetVisibility(Fade >= 1.f ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (TitleText)
	{
		// The headline tightens from wide tracking into place.
		FSlateFontInfo Font = TitleText->GetFont();
		Font.LetterSpacing = FMath::RoundToInt(FMath::Lerp(160.f, 20.f, Ease(Elapsed, 0.2f, 1.1f)));
		TitleText->SetFont(Font);
	}
	if (SidePanel)
	{
		const float Slide = Ease(Elapsed, 0.f, 0.28f);
		SidePanel->SetRenderTranslation(FVector2D((1.f - Slide) * -PanelWidth, 0.f));
	}
	const float Start = Mode == ESSMenuMode::FrontEnd ? 0.35f : 0.1f;
	for (int32 Index = 0; Index < Animated.Num(); ++Index)
	{
		Reveal(Animated[Index], Ease(Elapsed, Start + 0.05f * Index, 0.35f));
	}
}

void USSMenuWidget::SetBots(int32 Count)
{
	SelectedBots = Count;
	const int32 Values[] = { 4, 8, 12 };
	for (int32 Index = 0; Index < BotButtons.Num(); ++Index)
	{
		const bool bOn = Values[Index] == Count;
		StyleButton(BotButtons[Index], bOn ? SSPalette::Brass500(0.95f) : SSPalette::Field800(0.9f),
			bOn ? SSPalette::Brass300() : SSPalette::Field700(0.98f), FMargin(8.f, 8.f));
	}
}

void USSMenuWidget::PlayMap(const UObject* Context, const TCHAR* Map)
{
	if (APlayerController* Player = UGameplayStatics::GetPlayerController(Context, 0))
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
	UGameplayStatics::OpenLevel(Context, FName(Map), /*bAbsolute=*/ true,
		FString::Printf(TEXT("NumBots=%d%s"), SelectedBots, bSelectedSectionRules ? TEXT("?Rules=Section") : TEXT("")));
}

void USSMenuWidget::SetSectionRules(bool bSection)
{
	bSelectedSectionRules = bSection;
	for (int32 Index = 0; Index < RulesButtons.Num(); ++Index)
	{
		const bool bOn = (Index == 1) == bSection;
		StyleButton(RulesButtons[Index], bOn ? SSPalette::Brass500(0.95f) : SSPalette::Field800(0.9f),
			bOn ? SSPalette::Brass300() : SSPalette::Field700(0.98f), FMargin(12.f, 8.f));
	}
}

void USSMenuWidget::OnRedGum()   { PlayMap(this, TEXT("/Game/Maps/L_RedGum_01")); }
void USSMenuWidget::OnDryRiver() { PlayMap(this, TEXT("/Game/Maps/L_DryRiver_01")); }
void USSMenuWidget::OnSaltbush()  { PlayMap(this, TEXT("/Game/Maps/L_Saltbush_01")); }
void USSMenuWidget::OnSelatCanal() { PlayMap(this, TEXT("/Game/Maps/L_SelatCanal_01")); }
void USSMenuWidget::OnBluestone()  { PlayMap(this, TEXT("/Game/Maps/L_Bluestone_01")); }
void USSMenuWidget::OnBots4()    { SetBots(4); }
void USSMenuWidget::OnBots8()    { SetBots(8); }
void USSMenuWidget::OnBots12()   { SetBots(12); }
void USSMenuWidget::OnRulesObjective() { SetSectionRules(false); }
void USSMenuWidget::OnRulesSection()   { SetSectionRules(true); }

void USSMenuWidget::OnSettings()
{
	if (!Settings)
	{
		Settings = CreateWidget<USSSettingsWidget>(GetOwningPlayer(), USSSettingsWidget::StaticClass());
		if (!Settings)
		{
			return;
		}
		Settings->AddToViewport(70);
		TWeakObjectPtr<USSMenuWidget> WeakThis(this);
		Settings->OnClosed = [WeakThis]()
		{
			if (USSMenuWidget* Menu = WeakThis.Get())
			{
				Menu->Content->SetVisibility(ESlateVisibility::Visible);
				Menu->Replay();
			}
		};
	}
	Settings->SetVisibility(ESlateVisibility::Visible);
	Settings->Replay();
	Content->SetVisibility(ESlateVisibility::Hidden);
}

void USSMenuWidget::OnResume()
{
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
	if (Settings)
	{
		Settings->SetVisibility(ESlateVisibility::Collapsed);
	}
	SetVisibility(ESlateVisibility::Collapsed);
}

void USSMenuWidget::OnRedeploy()
{
	// Ends this life (the bridge asks the server); the class selection follows, as after any death.
	if (USSLocalHudState* State = GetWorld() ? GetWorld()->GetSubsystem<USSLocalHudState>() : nullptr)
	{
		State->bRedeployRequested = true;
		State->LastRedeployTime = GetWorld()->GetTimeSeconds();
	}
	OnResume();
}

void USSMenuWidget::OnMainMenu()
{
	UGameplayStatics::OpenLevel(this, FName(FrontEndMap), /*bAbsolute=*/ true);
}

void USSMenuWidget::OnDiscord()
{
	FPlatformProcess::LaunchURL(TEXT("https://discord.gg/GHNCFQrDND"), nullptr, nullptr);
}

void USSMenuWidget::OnQuit()
{
	UKismetSystemLibrary::QuitGame(this, GetOwningPlayer(), EQuitPreference::Quit, false);
}
